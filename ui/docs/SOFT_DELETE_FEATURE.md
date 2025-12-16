# Soft Delete Feature for Jobs

## Overview

Users can now delete jobs from their job list, but the jobs are not actually removed from the system. Instead, they are marked as "deleted" and hidden from the user's view while being kept for statistical analysis.

## Features

### For Users

**Delete Single or Multiple Jobs:**
- Select jobs using checkboxes in the job list
- Click "Delete Selected" button
- Confirm deletion
- Jobs are immediately hidden from the list

**What Happens:**
- Jobs are marked with `deleted: true` in metadata
- Deletion timestamp is recorded (`deleted_at`)
- User ID who deleted the job is recorded (`deleted_by`)
- Jobs remain on disk and in the database
- Jobs are hidden from user's job list

### For Administrators

**View Deleted Jobs:**
- Access `/admin/deleted-jobs` route
- See all deleted jobs across all users
- View deletion timestamps and who deleted them
- Use for statistical analysis

**Statistics Available:**
- Total number of deleted jobs
- When jobs were deleted
- Who deleted them
- Original job metadata (submission time, files, etc.)

## Implementation Details

### Database Changes

Jobs metadata now includes:
```json
{
  "job_name": "example_job",
  "job_id": "12345",
  "deleted": true,
  "deleted_at": "2025-12-16T10:30:00",
  "deleted_by": "user-uuid-here",
  ...
}
```

### API Endpoints

**`POST /delete-jobs`**
- Soft deletes one or multiple jobs
- Requires authentication
- Users can only delete their own jobs
- Admins can delete any job

**`GET /admin/deleted-jobs`**
- View all deleted jobs (admin only)
- For statistical analysis

### Frontend Changes

**Jobs List Page (`/jobs`):**
- Added "Delete Selected" button
- Appears when jobs are selected
- Confirmation dialog before deletion
- Page reloads after successful deletion

**Admin Dashboard:**
- Link to view deleted jobs
- Statistics on deleted jobs

## Security

- Users can only delete their own jobs
- Admins can delete any job
- Deleted jobs are not physically removed
- Access control enforced on all endpoints
- Deletion is logged with user ID and timestamp

## Benefits

1. **User Experience:** Users can clean up their job list
2. **Data Retention:** Jobs are kept for analysis
3. **Statistics:** Track job deletion patterns
4. **Audit Trail:** Know who deleted what and when
5. **Reversible:** Jobs can be "undeleted" if needed (admin function)

## Future Enhancements

### Possible Additions:

1. **Restore Deleted Jobs:**
   - Admin function to restore deleted jobs
   - User function to restore their own deleted jobs (within timeframe)

2. **Auto-Delete Old Jobs:**
   - Automatically soft-delete jobs older than X days
   - Configurable per user or globally

3. **Permanent Delete:**
   - Admin function to permanently remove old deleted jobs
   - After a certain period (e.g., 1 year)

4. **Deletion Statistics Dashboard:**
   - Charts showing deletion patterns
   - Most deleted job types
   - User deletion behavior

5. **Bulk Operations:**
   - Delete all completed jobs
   - Delete all failed jobs
   - Delete jobs older than date

## Usage Examples

### User Deleting Jobs

1. Go to "My Jobs" page
2. Select jobs to delete using checkboxes
3. Click "Delete Selected (N)" button
4. Confirm deletion
5. Jobs disappear from list

### Admin Viewing Deleted Jobs

1. Go to Admin Dashboard
2. Click "View Deleted Jobs"
3. See all deleted jobs with metadata
4. Use for analysis or reporting

### Checking Deletion Statistics

```python
# Count deleted jobs
deleted_count = sum(1 for job in all_jobs if job.get('deleted', False))

# Get deletion timeline
deletions_by_date = {}
for job in all_jobs:
    if job.get('deleted'):
        date = job.get('deleted_at', '')[:10]
        deletions_by_date[date] = deletions_by_date.get(date, 0) + 1
```

## Technical Notes

### Why Soft Delete?

- **Data Integrity:** Preserves historical data
- **Analytics:** Enables usage pattern analysis
- **Compliance:** May be required for audit purposes
- **Recovery:** Allows restoration if needed
- **Statistics:** Track system usage accurately

### Performance Considerations

- Deleted jobs are filtered at query time
- Minimal performance impact (simple boolean check)
- Can be optimized with database indexing if needed
- Consider archiving very old deleted jobs

### Storage Considerations

- Deleted jobs still consume disk space
- Implement periodic cleanup for old deleted jobs
- Monitor disk usage
- Consider compression for old deleted jobs

## Testing

### Test Cases

1. **User can delete own job**
   - Select job
   - Click delete
   - Verify job is hidden
   - Verify metadata has deleted flag

2. **User cannot delete other user's job**
   - Try to delete via API
   - Verify access denied

3. **Admin can delete any job**
   - Select any job
   - Delete successfully

4. **Multiple jobs can be deleted**
   - Select multiple jobs
   - Delete all at once
   - Verify all are hidden

5. **Deleted jobs appear in admin view**
   - Delete a job
   - Check admin deleted jobs page
   - Verify job appears

6. **Deleted jobs don't appear in user list**
   - Delete a job
   - Refresh job list
   - Verify job is gone

## Conclusion

The soft delete feature provides a user-friendly way to manage jobs while preserving data for administrative and statistical purposes. It balances user needs (clean interface) with system needs (data retention and analysis).

---

**Related Documentation:**
- [Job Management](../README.md#job-management)
- [Admin Features](../README.md#admin-features)
