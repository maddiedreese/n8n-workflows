#!/usr/bin/env python3
"""
Build script to extract workflow data from n8n JSON files.
Processes all *.json files and outputs a single workflows.json file.
"""

import json
import os
import glob
import re
from datetime import datetime
from pathlib import Path

def slugify(text):
    """Convert text to URL-friendly slug"""
    return re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')

def load_search_categories():
    """Load category mappings if available"""
    categories = {
        'marketing': ['lead', 'email', 'campaign', 'social', 'content', 'seo', 'analytics'],
        'sales': ['crm', 'deal', 'quote', 'invoice', 'customer', 'sales', 'pipeline'],
        'business-intelligence': ['report', 'dashboard', 'analytics', 'data', 'bi', 'metrics'],
        'automation': ['workflow', 'process', 'trigger', 'schedule', 'notification'],
        'communication': ['slack', 'email', 'chat', 'notification', 'message'],
        'finance': ['stripe', 'paypal', 'invoice', 'payment', 'accounting'],
        'productivity': ['calendar', 'task', 'todo', 'reminder', 'scheduling'],
        'e-commerce': ['shopify', 'woocommerce', 'product', 'order', 'inventory'],
        'hr': ['employee', 'recruitment', 'onboarding', 'time', 'leave'],
        'support': ['ticket', 'helpdesk', 'zendesk', 'support', 'customer-service']
    }
    return categories

def categorize_workflow(name, description, integrations):
    """Determine workflow category based on content"""
    categories = load_search_categories()
    text = f"{name} {description} {' '.join(integrations)}".lower()
    
    # Score each category
    scores = {}
    for category, keywords in categories.items():
        score = sum(1 for keyword in keywords if keyword in text)
        if score > 0:
            scores[category] = score
    
    # Return highest scoring category or default
    if scores:
        return max(scores.items(), key=lambda x: x[1])[0]
    return 'automation'

def extract_integrations(workflow_data):
    """Extract integration names from workflow nodes"""
    integrations = set()
    
    if 'nodes' in workflow_data:
        for node in workflow_data['nodes']:
            if 'type' in node:
                node_type = node['type']
                # Clean up node type names
                if node_type.startswith('n8n-nodes-'):
                    node_type = node_type.replace('n8n-nodes-', '')
                if node_type.startswith('base.'):
                    node_type = node_type.replace('base.', '')
                
                # Capitalize and clean
                integration = node_type.replace('-', ' ').title()
                integrations.add(integration)
    
    return list(integrations)[:5]  # Limit to first 5 integrations

def process_workflow_file(file_path):
    """Process a single workflow JSON file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Extract basic info
        name = data.get('name', Path(file_path).stem)
        description = data.get('description', '')
        if not description:
            description = f"Automated workflow for {name.lower()}"
        
        # Extract integrations
        integrations = extract_integrations(data)
        
        # Generate metadata
        slug = slugify(name)
        category = categorize_workflow(name, description, integrations)
        
        # Get file modification time or use workflow updatedAt
        updated_at = data.get('updatedAt')
        if not updated_at:
            stat = os.stat(file_path)
            updated_at = datetime.fromtimestamp(stat.st_mtime).isoformat()
        
        workflow = {
            'slug': slug,
            'name': name,
            'description': description,
            'integrations': integrations,
            'category': category,
            'gh_path': str(Path(file_path).relative_to('.')),
            'updated_at': updated_at
        }
        
        return workflow
        
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return None

def main():
    """Main build function"""
    print("Building workflows.json from n8n workflow files...")
    
    # Find all JSON files (excluding package.json, etc.)
    workflow_files = []
    for pattern in ['**/*.json', 'workflows/**/*.json', 'n8n/**/*.json']:
        files = glob.glob(pattern, recursive=True)
        workflow_files.extend([f for f in files if not any(exclude in f for exclude in [
            'package.json', 'package-lock.json', 'tsconfig.json', 'node_modules'
        ])])
    
    # Remove duplicates
    workflow_files = list(set(workflow_files))
    
    print(f"Found {len(workflow_files)} workflow files")
    
    # Process all workflows
    workflows = []
    for file_path in workflow_files:
        workflow = process_workflow_file(file_path)
        if workflow:
            workflows.append(workflow)
    
    print(f"Successfully processed {len(workflows)} workflows")
    
    # Create output directory
    os.makedirs('public', exist_ok=True)
    
    # Write output
    output_data = {
        'workflows': workflows,
        'total_count': len(workflows),
        'categories': list(set(w['category'] for w in workflows)),
        'generated_at': datetime.now().isoformat(),
        'version': '1.0'
    }
    
    with open('public/workflows.json', 'w', encoding='utf-8') as f:
        json.dump(output_data, f, separators=(',', ':'), ensure_ascii=False)
    
    print(f"Generated public/workflows.json with {len(workflows)} workflows")
    print(f"Categories found: {', '.join(output_data['categories'])}")

if __name__ == '__main__':
    main()
