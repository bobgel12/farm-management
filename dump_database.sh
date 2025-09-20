#!/bin/bash

# Script to dump the current database data
# Usage: ./dump_database.sh [output_file]

set -e

# Default output file
OUTPUT_FILE=${1:-"database_dump_$(date +%Y%m%d_%H%M%S).sql"}

echo "🗄️  Dumping database to $OUTPUT_FILE..."

# Check if containers are running
if ! docker-compose ps | grep -q "chicken_house_management-db-1.*Up"; then
    echo "❌ Database container is not running. Please start the application first."
    exit 1
fi

# Create the dump
docker-compose exec -T db pg_dump -U postgres -d chicken_management > "$OUTPUT_FILE"

# Check if dump was successful
if [ -s "$OUTPUT_FILE" ]; then
    echo "✅ Database dump created successfully: $OUTPUT_FILE"
    echo "📊 Dump size: $(du -h "$OUTPUT_FILE" | cut -f1)"
    
    # Show some stats about the dump
    echo "📈 Dump statistics:"
    echo "   - Total lines: $(wc -l < "$OUTPUT_FILE")"
    echo "   - Farms: $(grep -c "INSERT INTO.*farms_farm" "$OUTPUT_FILE" || echo "0")"
    echo "   - Houses: $(grep -c "INSERT INTO.*houses_house" "$OUTPUT_FILE" || echo "0")"
    echo "   - Tasks: $(grep -c "INSERT INTO.*tasks_task" "$OUTPUT_FILE" || echo "0")"
    echo "   - Workers: $(grep -c "INSERT INTO.*farms_worker" "$OUTPUT_FILE" || echo "0")"
else
    echo "❌ Failed to create database dump"
    exit 1
fi

