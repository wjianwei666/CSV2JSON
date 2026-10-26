CSV2JSON is a lightweight, professional-grade command-line tool that converts 
CSV files into clean, well-structured JSON in a single command. Built entirely 
on Python's standard library, it requires zero external dependencies — just 
download and run.

Unlike basic converters that dump everything as strings, CSV2JSON intelligently 
infers data types: integers, floats, booleans, and null values are automatically 
detected and properly typed in the output JSON. This means your "age" column 
becomes numbers, your "active" column becomes true/false, and empty cells are 
handled gracefully.

Whether you need to process a single file, batch-convert an entire directory of 
CSVs, or pipe data through stdin in a shell pipeline, CSV2JSON handles it all 
with clear error messages and flexible encoding support (UTF-8, GBK, Latin-1, 
UTF-16, and more).

Key highlights:
• 212 lines of clean, well-commented Python — easy to audit and customize
• Smart type inference (int / float / bool / null / string)
• Three input modes: single file, batch directory, or stdin pipe
• Multi-encoding support with configurable error handling
• Pretty-printed or compact JSON output
• Graceful error recovery with --skip-bad-rows flag
• MIT licensed — free for personal and commercial use

Perfect for developers, data analysts, and anyone who needs to bridge the gap 
between CSV data and JSON-based applications, APIs, or databases.
