import pandas as pd
import os
from typing import List, Dict, Any
from agents import function_tool

try:
    _jobs_df = pd.read_csv("jobs.csv") if os.path.exists("jobs.csv") else pd.DataFrame()
    print(f"Loaded {len(_jobs_df)} jobs from jobs.csv")
except Exception as e:
    print(f"Error loading jobs: {e}")
    _jobs_df = pd.DataFrame()

@function_tool
def search_jobs(keywords: str = "", location: str = "", max_results: int = 10) -> List[Dict[str, Any]]:
    """Search for jobs based on keywords and location."""
    
    if _jobs_df.empty:
        return [{"title": "No jobs available", "company": "", "location": "", "url": ""}]
    
    df = _jobs_df.copy()
    
    if keywords:
        keyword_list = [k.strip().lower() for k in keywords.split() if k.strip()]
        if keyword_list:
            mask = df['job_title'].str.lower().str.contains('|'.join(keyword_list), na=False, regex=True)
            df = df[mask]
    
    if location:
        location_mask = df['job_location'].str.lower().str.contains(location.lower(), na=False)
        df = df[location_mask]
    
    if 'job_posted_date' in df.columns:
        df = df.sort_values('job_posted_date', ascending=False)
    
    results = []
    for _, row in df.head(max_results).iterrows():
        company_name = row.get('prospect_domain', 'Unknown Company')
        if company_name and company_name != 'Unknown Company':
            company_name = company_name.replace('.com', '').replace('.io', '').replace('.org', '').title()
        
        results.append({
            'title': row['job_title'],
            'company': company_name,
            'location': row['job_location'],
            'url': row['job_url'],
            'posted_date': row.get('job_posted_date', 'Recently')
        })
    
    return results if results else [{"title": "No matching jobs found", "company": "", "location": "", "url": ""}]

@function_tool
def get_job_categories() -> List[str]:
    """Get available job categories from the database."""
    if _jobs_df.empty:
        return []
    
    titles = _jobs_df['job_title'].dropna().unique()
    categories = set()
    
    for title in titles:
        parts = title.replace('|', ' ').replace('-', ' ').split()
        for part in parts:
            part = part.strip().lower()
            if len(part) > 2 and part not in ['all', 'levels', 'senior', 'junior', 'mid']:
                categories.add(part.title())
    
    return sorted(list(categories))[:15]

@function_tool
def get_recent_jobs(max_results: int = 10) -> List[Dict[str, Any]]:
    """Get the most recent job postings."""
    
    if _jobs_df.empty:
        return [{"title": "No jobs available", "company": "", "location": "", "url": ""}]
    
    df = _jobs_df.copy()
    
    if 'job_posted_date' in df.columns:
        df = df.sort_values('job_posted_date', ascending=False)
    
    results = []
    for _, row in df.head(max_results).iterrows():
        company_name = row.get('prospect_domain', 'Unknown Company')
        if company_name and company_name != 'Unknown Company':
            company_name = company_name.replace('.com', '').replace('.io', '').replace('.org', '').title()
        
        results.append({
            'title': row['job_title'],
            'company': company_name,
            'location': row['job_location'],
            'url': row['job_url'],
            'posted_date': row.get('job_posted_date', 'Recently')
        })
    
    return results
