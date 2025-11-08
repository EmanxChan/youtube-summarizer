#!/usr/bin/env python3
"""
Slash-command CLI entry point for Droid.
Parses slash commands and delegates to appropriate handlers.
"""
import sys
from pathlib import Path


def print_usage():
    """Print usage information"""
    print("Usage: python droid_slash_cli.py /<command> [arguments]")
    print("\nAvailable commands:")
    print("  /youtube <url|search_query> [--words N]  - Summarize YouTube video")
    print("\nExamples:")
    print('  python droid_slash_cli.py /youtube "https://www.youtube.com/watch?v=dQw4w9WgXcQ"')
    print('  python droid_slash_cli.py /youtube "machine learning tutorial" --words 200')


def main():
    if len(sys.argv) < 2:
        print("Error: No command provided", file=sys.stderr)
        print_usage()
        sys.exit(1)
    
    command = sys.argv[1]
    
    # Validate slash command format
    if not command.startswith('/'):
        print(f"Error: Command must start with '/' (got: {command})", file=sys.stderr)
        print_usage()
        sys.exit(1)
    
    # Extract command name
    command_name = command[1:].lower()
    
    # Route to appropriate handler
    if command_name == 'youtube':
        if len(sys.argv) < 3:
            print("Error: /youtube requires a URL or search query", file=sys.stderr)
            print_usage()
            sys.exit(1)
        
        # Import and delegate to youtube handler
        try:
            from youtube_slash_command import handle_youtube_command
            remaining_args = sys.argv[2:]
            sys.exit(handle_youtube_command(remaining_args))
        except ImportError as e:
            print(f"Error: Failed to import youtube handler: {e}", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
    
    elif command_name in ['help', '-h', '--help']:
        print_usage()
        sys.exit(0)
    
    else:
        print(f"Error: Unknown command '/{command_name}'", file=sys.stderr)
        print_usage()
        sys.exit(1)


if __name__ == "__main__":
    main()
