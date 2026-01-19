"""
Parse installer data from CSV and generate bulk import data.
Python equivalent of parse-installers.js
"""
import csv
import json
import re
from pathlib import Path


def parse_coverage(state_str):
    """Parse operational state/coverage areas."""
    if not state_str:
        return []
    
    coverage = []
    normalized = state_str.strip().upper()
    
    if 'C1' in normalized or 'CENTRAL 1' in normalized:
        coverage.append('C1')
    if 'C2' in normalized or 'CENTRAL 2' in normalized:
        coverage.append('C2')
    if any(x in normalized for x in ['NORTHEN', 'NORTHERN', 'PERAK', 'KEDAH', 'PERLIS', 'PULAU PINANG']):
        if 'Northen' not in coverage:
            coverage.append('Northen')
    if any(x in normalized for x in ['SOUTHERN', 'N.SEMBILAN', 'MELAKA', 'JOHOR']):
        if 'Southern' not in coverage:
            coverage.append('Southern')
    if any(x in normalized for x in ['EAST COAST', 'PAHANG', 'TERENGGANU', 'KELANTAN']):
        if 'East Coast' not in coverage:
            coverage.append('East Coast')
    if any(x in normalized for x in ['EAST M', 'SABAH', 'SARAWAK']):
        if "East M'sia" not in coverage:
            coverage.append("East M'sia")
    
    return coverage if coverage else ['Unknown']


def clean_email(email):
    """Clean email address."""
    if not email:
        return ''
    # Remove extra text after space or comma
    return email.split(' ')[0].split(',')[0].strip()


def clean_phone(phone):
    """Clean phone number."""
    if not phone:
        return '0000000000'
    # Remove spaces, dashes, and non-digits
    return re.sub(r'[^\d]', '', phone.replace(' ', '').replace('-', ''))


def parse_csv_file(csv_path):
    """Parse CSV file and extract installer data."""
    installers = []
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        # Skip header rows (lines 0-7)
        for _ in range(8):
            next(f, None)
        
        # Read remaining lines
        reader = csv.reader(f)
        current_address = ''
        in_multi_line_address = False
        
        for row in reader:
            if not row or not any(row):
                continue
            
            # Check if this is a new data row (starts with empty first column and date pattern)
            if len(row) > 1 and row[0] == '' and re.match(r'\d{2}/\d{2}/\d{4}', row[1] if len(row) > 1 else ''):
                try:
                    timestamp = row[1] if len(row) > 1 else ''
                    company = (row[2] if len(row) > 2 else '').strip()
                    ssm_number = row[3] if len(row) > 3 else ''
                    year_established = row[4] if len(row) > 4 else ''
                    address = (row[5] if len(row) > 5 else '').strip()
                    coverage_str = row[6] if len(row) > 6 else ''
                    name = row[7] if len(row) > 7 else ''
                    designation = row[8] if len(row) > 8 else ''
                    phone = clean_phone(row[9] if len(row) > 9 else '')
                    email = clean_email(row[10] if len(row) > 10 else '')
                    
                    # Handle multi-line addresses (if address field contains unclosed quotes)
                    if address.startswith('"') and not address.endswith('"'):
                        # This is a simplified version - full implementation would handle multi-line
                        address = address.replace('"', '').strip()
                    
                    # Only add if we have required fields
                    if email and '@' in email and company:
                        installer = {
                            'company': company,
                            'name': name or company.split(' ')[0],
                            'email': email.lower(),
                            'phone': phone or '0000000000',
                            'address': address or 'Unknown',
                            'coverage': parse_coverage(coverage_str),
                            'specialties': ['EV Charger Installation'],
                            'certifications': []
                        }
                        installers.append(installer)
                except Exception as e:
                    print(f"Error parsing row: {e}")
                    continue
    
    # Remove duplicates based on email
    unique_installers = []
    email_map = {}
    
    for inst in installers:
        existing = email_map.get(inst['email'])
        
        if not existing:
            email_map[inst['email']] = inst
            unique_installers.append(inst)
        else:
            # Prefer the one with better address/company name
            if existing['address'] == 'Unknown' and inst['address'] != 'Unknown':
                index = unique_installers.index(existing)
                unique_installers[index] = inst
                email_map[inst['email']] = inst
            elif len(existing['company']) < len(inst['company']):
                # Prefer longer company name (more complete)
                index = unique_installers.index(existing)
                unique_installers[index] = inst
                email_map[inst['email']] = inst
    
    return unique_installers


def create_postman_collection(installers, output_path):
    """Create Postman collection for bulk import."""
    collection = {
        'info': {
            'name': 'Bulk Import Installers',
            'description': f'Import {len(installers)} installer records from CSV',
            'schema': 'https://schema.getpostman.com/json/collection/v2.1.0/collection.json'
        },
        'item': [
            {
                'name': 'Bulk Import Installers',
                'request': {
                    'method': 'POST',
                    'header': [
                        {
                            'key': 'Content-Type',
                            'value': 'application/json'
                        },
                        {
                            'key': 'Authorization',
                            'value': 'Bearer {{authToken}}',
                            'description': 'Get token from login request first'
                        }
                    ],
                    'body': {
                        'mode': 'raw',
                        'raw': json.dumps({'installers': installers}, indent=2)
                    },
                    'url': {
                        'raw': '{{baseUrl}}/api/installers/bulk-import',
                        'host': ['{{baseUrl}}'],
                        'path': ['api', 'installers', 'bulk-import']
                    },
                    'description': f'Bulk import {len(installers)} installers from the CSV data. This will create User accounts and Installer profiles for each entry. Default password: Installer123!'
                },
                'response': []
            }
        ],
        'variable': [
            {
                'key': 'baseUrl',
                'value': 'https://installation-system-backend.onrender.com',
                'type': 'string'
            },
            {
                'key': 'authToken',
                'value': '',
                'type': 'string',
                'description': 'Set this after logging in'
            }
        ]
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(collection, f, indent=2, ensure_ascii=False)
    
    return output_path


def main():
    """Main function."""
    # Get CSV file path
    csv_path = Path(__file__).parent.parent / 'Mock Data Installer  - Sheet1.csv'
    
    if not csv_path.exists():
        print(f"CSV file not found: {csv_path}")
        return
    
    print(f"Reading CSV file: {csv_path}")
    installers = parse_csv_file(csv_path)
    
    print(f"\n✅ Parsed {len(installers)} total installers")
    
    # Count by coverage
    coverage_count = {}
    for inst in installers:
        for cov in inst['coverage']:
            coverage_count[cov] = coverage_count.get(cov, 0) + 1
    
    print(f"\n📊 Coverage breakdown:")
    for cov, count in sorted(coverage_count.items()):
        print(f"   {cov}: {count}")
    
    # Create Postman collection
    output_path = Path(__file__).parent / 'POSTMAN_BULK_IMPORT_INSTALLERS.json'
    create_postman_collection(installers, output_path)
    
    print(f"\n✅ Postman collection created: {output_path}")
    print(f"\nTotal unique installers: {len(installers)}")
    print(f"\nSample installers (first 5):")
    for idx, inst in enumerate(installers[:5], 1):
        print(f"\n{idx}. {inst['company']}")
        print(f"   Name: {inst['name']}")
        print(f"   Email: {inst['email']}")
        print(f"   Phone: {inst['phone']}")
        print(f"   Coverage: {', '.join(inst['coverage'])}")


if __name__ == '__main__':
    main()
