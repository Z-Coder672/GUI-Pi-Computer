from decimal import getcontext, Decimal
import time
import argparse
import sys
import os
from datetime import timedelta

class PiCalculator:
    def __init__(self):
        self.running = False
        self.precision = 100
        self.current_value = None
        self.start_time = None
        self.pi = None
        
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
        
    def calculate_pi(self):
        self.running = True
        self.start_time = time.time_ns()
        
        excess_prec = 2
        prec_cur = 100 if self.precision > 100 else self.precision
        getcontext().prec = prec_cur + excess_prec
        
        second = Decimal(3)  # Current element for PI
        queue_cur = [Decimal(0), Decimal(0), Decimal(0), second]
        
        qq_append = queue_cur.append
        qq_pop = queue_cur.pop
        
        limit = Decimal(10) ** (-prec_cur - excess_prec)
        iteration = 0
        last_update = 0
        
        print(f"Calculating π to {self.precision} digits...")
        print("Progress: 0%", end='\r')
        
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
                
                # Update progress every 100 iterations
                if iteration % 100 == 0:
                    progress = (prec_cur / self.precision) * 100
                    elapsed = (time.time_ns() - self.start_time) / 1_000_000_000
                    print(f"Progress: {progress:.1f}% | Elapsed: {self.format_time(elapsed)}", end='\r')
                    sys.stdout.flush()
            
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
            return self.current_value
        return None
    
    def stop(self):
        self.running = False
    
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
        return f"{time_str}.{milliseconds:03d}"

def save_result(value, filename="pi.txt"):
    """Save the result to a file"""
    try:
        with open(filename, "w") as f:
            f.write(str(value))
        print(f"\nResult saved to {filename}")
    except Exception as e:
        print(f"\nError saving file: {str(e)}")

def main():
    parser = argparse.ArgumentParser(description='Calculate π to specified precision')
    parser.add_argument('digits', type=int, help='Number of digits to calculate')
    parser.add_argument('--output', '-o', default='pi.txt', help='Output file name (default: pi.txt)')
    parser.add_argument('--no-save', action='store_true', help='Don\'t save the result to a file')
    args = parser.parse_args()
    
    if args.digits < 1:
        print("Error: Number of digits must be positive")
        sys.exit(1)
    
    calculator = PiCalculator()
    calculator.precision = args.digits
    
    try:
        result = calculator.calculate_pi()
        if result is None:
            print("\nCalculation stopped.")
            return
        
        elapsed = (time.time_ns() - calculator.start_time) / 1_000_000_000
        print(f"\nCalculation complete! Time: {calculator.format_time(elapsed)}")
        print(f"\nπ = {result}")
        
        # Verify result if precision <= 10000
        if calculator.precision <= 10000:
            verification = calculator.verify_result(result)
            if verification is None:
                print("\nVerification skipped: Da_actual_pi.txt not found")
            else:
                is_correct, position = verification
                if is_correct:
                    print("\n✓ Result verified correct!")
                else:
                    print(f"\n✗ Error at position {position} (counting from 0)")
        
        # Save result if requested
        if not args.no_save:
            save_result(result, args.output)
            
    except KeyboardInterrupt:
        print("\nCalculation interrupted by user.")
        calculator.stop()
    except Exception as e:
        print(f"\nError during calculation: {str(e)}")
        calculator.stop()

if __name__ == "__main__":
    main() 