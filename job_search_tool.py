import pandas as pd
import os
from typing import List, Dict, Any
from agents import function_tool

# Load jobs data with error handling
try:
    _jobs_df = pd.read_csv("jobs.csv") if os.path.exists("jobs.csv") else pd.DataFrame()
    print(f"✅ Loaded {len(_jobs_df)} jobs from jobs.csv")
except Exception as e:
    print(f"⚠️  Error loading jobs: {e}")
    _jobs_df = pd.DataFrame()

@function_tool
def search_jobs(keywords: str = "", location: str = "", max_results: int = 5) -> List[Dict[str, Any]]:
    """Search for jobs based on keywords and location.
    
    Args:
        keywords: Keywords to search in job titles (e.g., "python", "backend")
        location: Location filter (e.g., "New York", "remote")
        max_results: Maximum jobs to return (default: 5)
    """
    if _jobs_df.empty:
        return [{"title": "No jobs available", "company": "", "location": "", "url": ""}]
    
    df = _jobs_df.copy()
    
    # Filter by keywords
    if keywords:
        df = df[df['job_title'].str.lower().str.contains(keywords.lower(), na=False)]
    
    # Filter by location
    if location:
        df = df[df['job_location'].str.lower().str.contains(location.lower(), na=False)]
    
    # Sort by most recent if date column exists
    if 'job_posted_date' in df.columns:
        df = df.sort_values('job_posted_date', ascending=False)
    
    # Return results with all useful fields
    results = []
    for _, row in df.head(max_results).iterrows():
        results.append({
            'title': row['job_title'],
            'company': row.get('company', 'Company'),
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
    
    # Extract unique job categories
    categories = _jobs_df['job_title'].str.extract(r'([A-Za-z\s]+)')[0].str.strip().unique()
    return [cat for cat in categories if cat and len(cat) > 2][:10]
