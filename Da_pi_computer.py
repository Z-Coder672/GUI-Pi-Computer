from decimal import getcontext, Decimal
import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
import time
from datetime import datetime, timedelta
import os

class PiCalculator:
    def __init__(self):
        self.running = False
        self.precision = 100
        self.current_value = None
        self.progress_callback = None
        self.completion_callback = None
        self.start_time = None
        
    def verify_result(self, calculated_pi):
        """Verify calculated pi against actual pi for precision <= 10000"""
        if self.precision > 10000:
            return None
            
        try:
            with open("Da_actual_pi.txt", "r") as f:
                actual_pi = f.read().strip()
                # Convert actual pi to Decimal and round to same precision
                actual_decimal = Decimal(actual_pi)
                getcontext().prec = self.precision
                actual_rounded = +actual_decimal  # This forces rounding to current precision
                
                # For n digits total, we want "3." plus (n-1) digits after decimal
                comparison_length = self.precision + 1  # +1 for decimal point
                calculated_str = str(calculated_pi)[:comparison_length]
                actual_str = str(actual_rounded)[:comparison_length]
                
                if calculated_str == actual_str:
                    return True, None
                else:
                    # Find first difference
                    for i, (c1, c2) in enumerate(zip(calculated_str, actual_str)):
                        if c1 != c2:
                            position = i
                            break
                    return False, position
        except FileNotFoundError:
            return None
        except Exception as e:
            return None
        
    def calculate_pi(self, progress_callback=None, completion_callback=None):
        self.running = True
        self.progress_callback = progress_callback
        self.completion_callback = completion_callback
        self.start_time = time.time_ns()  # Use nanosecond precision
        
        excess_prec = 2
        prec_cur = 100 if self.precision > 100 else self.precision
        getcontext().prec = prec_cur + excess_prec
        
        second = Decimal(3)  # Current element for PI
        queue_cur = [Decimal(0), Decimal(0), Decimal(0), second]
        
        qq_append = queue_cur.append
        qq_pop = queue_cur.pop
        
        limit = Decimal(10) ** (-prec_cur - excess_prec)
        iteration = 0
        
        while self.running:
            sec_sq = second * second
            term = second
            acc = second + term
            count = Decimal(1)
            
            while term > limit and self.running:
                term *= sec_sq / ((count + 1) * (count + 2))
                acc -= term
                
                term *= sec_sq / ((count + 3) * (count + 4))
                acc += term
                
                count += 4
                
                iteration += 1
                if iteration % 10 == 0 and self.progress_callback:
                    self.progress_callback(acc, prec_cur)
            
            if acc in queue_cur:
                if prec_cur < self.precision:
                    prec_cur += prec_cur
                    if prec_cur > self.precision:
                        prec_cur = self.precision
                    limit = Decimal(10) ** (-prec_cur - excess_prec)
                    getcontext().prec = prec_cur + excess_prec
                else:
                    second = acc
                    break
            
            qq_append(acc)
            qq_pop(0)
            second = acc
        
        if self.running:  # Only if not stopped manually
            getcontext().prec = self.precision
            self.current_value = +second
            if self.completion_callback:
                self.completion_callback(self.current_value)
    
    def stop(self):
        self.running = False

class PiCalculatorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("π Calculator")
        self.calculator = PiCalculator()
        self.calc_thread = None
        self.timer_id = None
        
        # Create main frame
        main_frame = ttk.Frame(root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Precision input
        ttk.Label(main_frame, text="Precision (digits):").grid(row=0, column=0, sticky=tk.W)
        self.precision_var = tk.StringVar(value="100")
        precision_entry = ttk.Entry(main_frame, textvariable=self.precision_var, width=10)
        precision_entry.grid(row=0, column=1, sticky=tk.W, padx=5)
        
        # Control buttons
        self.start_button = ttk.Button(main_frame, text="Start", command=self.start_calculation)
        self.start_button.grid(row=0, column=2, padx=5)
        
        self.stop_button = ttk.Button(main_frame, text="Stop", command=self.stop_calculation, state=tk.DISABLED)
        self.stop_button.grid(row=0, column=3, padx=5)
        
        # Timer display
        timer_frame = ttk.LabelFrame(main_frame, text="Time", padding="5")
        timer_frame.grid(row=1, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=5)
        
        # Elapsed time
        ttk.Label(timer_frame, text="Elapsed:").grid(row=0, column=0, sticky=tk.W)
        self.elapsed_var = tk.StringVar(value="00:00:00")
        ttk.Label(timer_frame, textvariable=self.elapsed_var).grid(row=0, column=1, sticky=tk.W, padx=5)
        
        # Estimated time remaining
        ttk.Label(timer_frame, text="Remaining:").grid(row=0, column=2, sticky=tk.W, padx=(20,0))
        self.remaining_var = tk.StringVar(value="--:--:--")
        ttk.Label(timer_frame, textvariable=self.remaining_var).grid(row=0, column=3, sticky=tk.W, padx=5)
        
        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress = ttk.Progressbar(main_frame, length=300, mode='determinate', variable=self.progress_var)
        self.progress.grid(row=2, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=10)
        
        # Result display
        result_frame = ttk.LabelFrame(main_frame, text="Results", padding="5")
        result_frame.grid(row=3, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=5)
        
        self.result_text = scrolledtext.ScrolledText(result_frame, width=50, height=10, wrap=tk.WORD)
        self.result_text.grid(row=0, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=5)
        
        # Verification result
        self.verify_var = tk.StringVar(value="")
        self.verify_label = ttk.Label(result_frame, textvariable=self.verify_var, font=('TkDefaultFont', 10, 'bold'))
        self.verify_label.grid(row=1, column=0, columnspan=4, sticky=tk.W)
        
        # Status label
        self.status_var = tk.StringVar(value="Ready")
        self.status_label = ttk.Label(main_frame, textvariable=self.status_var)
        self.status_label.grid(row=4, column=0, columnspan=4, sticky=tk.W)
        
        # Save button
        self.save_button = ttk.Button(main_frame, text="Save to File", command=self.save_result, state=tk.DISABLED)
        self.save_button.grid(row=5, column=0, columnspan=4, pady=5)
        
        # Configure grid
        for child in main_frame.winfo_children():
            child.grid_configure(padx=5, pady=5)
    
    def format_time(self, seconds):
        """Format seconds into HH:MM:SS.ms"""
        if seconds is None:
            return "--:--:--.---"
        
        # Split into whole seconds and milliseconds
        whole_seconds = int(seconds)
        milliseconds = int((seconds - whole_seconds) * 1000)
        
        # Format main time part
        time_str = str(timedelta(seconds=whole_seconds))
        # Add milliseconds
        return f"{time_str}.{milliseconds:02d}"
    
    def update_timer(self):
        """Update the timer display"""
        if not self.calculator.running:
            if self.timer_id:
                self.root.after_cancel(self.timer_id)
                self.timer_id = None
            return
        
        if self.calculator.start_time:
            elapsed = (time.time_ns() - self.calculator.start_time) / 1_000_000_000
            self.elapsed_var.set(self.format_time(elapsed))
            
            # Calculate estimated time remaining
            progress = self.progress_var.get()
            if progress > 0:
                total_estimated = elapsed / (progress / 100)
                remaining = total_estimated - elapsed
                self.remaining_var.set(self.format_time(remaining))
        
        # Schedule next update only if still running
        if self.calculator.running:
            self.timer_id = self.root.after(50, self.update_timer)  # Update every 50ms for smoother display
    
    def update_progress(self, current_value, current_precision):
        if not self.calculator.running:
            return
        
        # Update progress bar
        progress = (current_precision / self.calculator.precision) * 100
        self.progress_var.set(progress)
        
        # Update result display
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(tk.END, f"Current Value:\n{current_value}\n\n")
        self.result_text.insert(tk.END, f"Current Precision: {current_precision} digits")
        
        # Update status
        self.status_var.set(f"Computing... ({current_precision}/{self.calculator.precision} digits)")
        
        # Force update
        self.root.update_idletasks()
    
    def calculation_complete(self, final_value):
        # Stop the timer first
        self.calculator.running = False
        if self.timer_id:
            self.root.after_cancel(self.timer_id)
            self.timer_id = None
        
        self.progress_var.set(100)
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(tk.END, f"Final Value of π:\n{final_value}")
        
        # Verify result if precision <= 1,000,000,000
        if self.calculator.precision <= 1_000_000_000:
            verification = self.calculator.verify_result(final_value)
            if verification is None:
                self.verify_var.set("Verification skipped: Da_actual_pi.txt not found")
                self.verify_label.configure(foreground="gray")
            else:
                is_correct, position = verification
                if is_correct:
                    self.verify_var.set("✓ Result verified correct!")
                    self.verify_label.configure(foreground="green")
                else:
                    self.verify_var.set(f"✗ Error at position {position} (counting from 0)")
                    self.verify_label.configure(foreground="red")
        else:
            self.verify_var.set("")
        
        # Show final time
        elapsed = (time.time_ns() - self.calculator.start_time) / 1_000_000_000
        self.elapsed_var.set(self.format_time(elapsed))
        self.remaining_var.set("00:00:00")
        self.status_var.set(f"Calculation complete! Total time: {self.format_time(elapsed)}")
        
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.save_button.config(state=tk.NORMAL)
    
    def start_calculation(self):
        try:
            precision = int(self.precision_var.get())
            if precision < 1:
                raise ValueError("Precision must be positive")
        except ValueError as e:
            self.status_var.set(f"Error: {str(e)}")
            return
        
        self.calculator.precision = precision
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.save_button.config(state=tk.DISABLED)
        self.status_var.set("Starting calculation...")
        self.progress_var.set(0)
        
        # Reset displays
        self.elapsed_var.set("00:00:00")
        self.remaining_var.set("--:--:--")
        self.verify_var.set("")
        
        self.calc_thread = threading.Thread(
            target=self.calculator.calculate_pi,
            args=(self.update_progress, self.calculation_complete)
        )
        self.calc_thread.daemon = True
        self.calc_thread.start()
        
        # Start timer updates
        self.update_timer()
    
    def stop_calculation(self):
        # Disable stop button immediately to prevent multiple clicks
        self.stop_button.config(state=tk.DISABLED)
        self.status_var.set("Stopping...")
        
        # Cancel timer first
        if self.timer_id:
            self.root.after_cancel(self.timer_id)
            self.timer_id = None
        
        # Stop the calculator
        if self.calculator:
            self.calculator.stop()
        
        # Handle thread cleanup in a safe way
        if self.calc_thread and self.calc_thread.is_alive():
            try:
                self.calc_thread.join(timeout=1.0)  # Wait up to 1 second for thread to finish
            except Exception:
                pass  # Ignore any thread-related errors
        
        # Update UI state
        self.start_button.config(state=tk.NORMAL)
        self.remaining_var.set("--:--:--")
        
        # Show final elapsed time
        if self.calculator.start_time:
            elapsed = (time.time_ns() - self.calculator.start_time) / 1_000_000_000
            self.elapsed_var.set(self.format_time(elapsed))
            self.status_var.set(f"Calculation stopped. Elapsed time: {self.format_time(elapsed)}")
        else:
            self.status_var.set("Calculation stopped.")
    
    def save_result(self):
        if not self.calculator.current_value:
            self.status_var.set("No result to save")
            return
        
        try:
            with open("pi.txt", "w") as f:
                f.write(str(self.calculator.current_value))
            self.status_var.set("Result saved to pi.txt")
        except Exception as e:
            self.status_var.set(f"Error saving file: {str(e)}")

def main():
    root = tk.Tk()
    app = PiCalculatorGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
