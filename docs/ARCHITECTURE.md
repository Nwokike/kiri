# Kiri Architecture: The "Zero-Local-File" Policy

**Date:** January 2026
**Version:** 1.0

## Core Philosophy
To maximize scalability and operate within the constraints of strict cloud environments (1GB RAM, ephemeral filesystems), Kiri adopts a **"GitHub-First"** storage strategy. We minimize local state and delegate content storage to GitHub.

## 1. Storage Strategy

### 1.1 Projects
- **Source of Truth**: The GitHub Repository.
- **Kiri Role**: Kiri acts as a viewer/editor interface. It does not "host" the code in its own database.
- **Syncing**: 
    - Viewing: Code is fetched via GitHub API.
    - Editing: Changes are committed directly to GitHub via API.
    - Cloning: Temporary clones in ephemeral `tmp/` directories for heavy analysis (Lane B/C).

### 1.2 Publications (New in Phase 4.5)
- **Content**: Stored as Markdown files in user's GitHub repositories (e.g., `username/my-kiri-papers`).
- **Media**: Images/Assets are committed to the same repository.
- **Database**: Stores metadata (title, abstract, stars) and a *pointer* (URL) to the GitHub file.
- **Rendering**: Kiri fetches the raw Markdown from GitHub and renders it.

### 1.3 User Files
- **Uploads**: Direct-to-GitHub (via API) or Direct-to-R2 (for profile pics).
- **No Local Storage**: We do not store user files on the application server disk.

## 2. Ephemeral Processing & Cleanup
Since some operations (like dependency analysis or building a container) require local files:
- **Location**: Use system temp directories (e.g., `/tmp/kiri_repos`).
- **Lifecycle**: Files exist only for the duration of the task.
- **Garbage Collection**: A periodic Huey task (`cleanup_tmp_files`) runs every 4 hours to forcefully remove any files older than 1 hour.

## 3. Benefits
1.  **Statelessness**: The app server can be killed/restarted without data loss.
2.  **Versioning**: Users get full Git history for their publications and projects for free.
3.  **Ownership**: Users own their data (in their GitHub), not locked into Kiri.
4.  **Cost**: Drastically reduces Kiri's storage costs (R2/S3 only for backups).

## 4. Implementation Details
- **Huey Task**: `kiri_project.tasks.cleanup_tmp_files`
- **Models**: `Publication` has `github_repo_url` field.
- **API**: Uses `projects.services.GitHubService` for all file interactions.
