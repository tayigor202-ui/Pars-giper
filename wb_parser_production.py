#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os, sys, time, random
from dotenv import load_dotenv
from wb_silent_parser import run_wb_silent_parsing, cleanup_resources
from wb_reporting import generate_wb_report, send_wb_report # New import

load_dotenv()

def main():
    print("="*70)
    print(" WILDBERRIES PRODUCTION PARSER (SILENT API ENGINE) ")
    print("="*70)
    
    try:
        run_wb_silent_parsing()
        
        # Report generation
        print("\n" + "="*70)
        report_file = generate_wb_report()
        if report_file:
            send_wb_report(report_file)
            
    except KeyboardInterrupt:
        print("\n[STOP] Parsing interrupted by user.")
    except Exception as e:
        print(f"\n[CRITICAL ERROR] {e}")
        import traceback
        traceback.print_exc()
    finally:
        cleanup_resources()

if __name__ == "__main__":
    main()
