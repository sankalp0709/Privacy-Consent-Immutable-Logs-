#!/usr/bin/env python3
"""
Git Secrets Cleanup Script
This script helps remove API keys and other secrets from git history.
Run this script to clean up accidentally committed secrets.
"""

import os
import subprocess
import sys

def run_command(cmd, description):
    """Run a shell command and return success status."""
    print(f"\n🔧 {description}")
    print(f"Command: {cmd}")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description} - SUCCESS")
            if result.stdout:
                print(result.stdout)
            return True
        else:
            print(f"❌ {description} - FAILED")
            if result.stderr:
                print(f"Error: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ {description} - ERROR: {str(e)}")
        return False

def main():
    """Main cleanup function."""
    print("🧹 Git Secrets Cleanup Script")
    print("=" * 50)
    print("This script will help remove accidentally committed API keys from git history.")
    print("⚠️  WARNING: This will rewrite git history. Make sure you have backups!")
    print()

    # Confirm with user
    response = input("Do you want to proceed with git history cleanup? (yes/no): ").lower().strip()
    if response not in ['yes', 'y']:
        print("❌ Cleanup cancelled by user.")
        return

    print("\n📋 Starting cleanup process...")

    # Step 1: Remove the .env.uniguru file from git tracking
    if os.path.exists('.env.uniguru'):
        success = run_command("git rm --cached .env.uniguru", "Remove .env.uniguru from git tracking")
        if not success:
            print("⚠️ Could not remove .env.uniguru from git. It may not be tracked.")

    # Step 2: Check if there are any other files with secrets
    print("\n🔍 Checking for other potential secret files...")
    secret_files = ['.env', '.env.local', '.env.production']
    for file in secret_files:
        if os.path.exists(file):
            print(f"⚠️ Found {file} - make sure it's in .gitignore")

    # Step 3: Force add .gitignore to ensure it's tracked
    run_command("git add .gitignore", "Add updated .gitignore")

    # Step 4: Create a new commit to remove the secrets
    commit_msg = "Remove API keys and secrets from repository"
    success = run_command(f'git commit -m "{commit_msg}"', "Commit the cleanup changes")

    if success:
        print("\n✅ Cleanup completed successfully!")
        print("📝 Next steps:")
        print("1. If you need to push to GitHub, use: git push --force-with-lease")
        print("2. If this is a shared repository, inform your collaborators to re-clone")
        print("3. Update your .env.uniguru file with your actual API keys (they won't be committed)")
        print("4. Consider rotating your API keys for security")
    else:
        print("\n❌ Cleanup may have issues. Check the output above.")

    print("\n🔒 Security Recommendations:")
    print("- Never commit API keys to version control")
    print("- Use environment variables for secrets")
    print("- Regularly rotate your API keys")
    print("- Use .env.example as a template, never commit .env files")

if __name__ == "__main__":
    main()