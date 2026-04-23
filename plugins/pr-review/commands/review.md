---
name: review
description: "Multi-agent PR review with voice-controlled comment posting. Specialized parallel agents review code, findings are walked through one at a time, and comments sound human. Use with /pr-review:review {url} or /pr-review:review for dashboard."
---

# PR Review

Multi-agent PR review pipeline with voice-controlled comment posting. Two modes: **dashboard** (no args) and **review** (PR URL or number from dashboard).

---

## Mode Detection

| Input | Mode |
|-------|------|
| No arguments | Dashboard: show all open PRs |
| PR URL (`https://github.com/...`) | Review that PR |
| Number from dashboard (e.g. "3") | Review that PR from the dashboard list |

---

## Dashboard Mode

When invoked with no arguments:

1. Fetch all open PRs across repos using `gh pr list --repo {repo} --state open --json number,title,author,headRefName,createdAt,reviewRequests`
2. Group by repo
3. Number rows **sequentially across all repos** so the user can say "review #3"
4. Sort by age (oldest first) within each group
5. Show: `#`, PR number, title (truncated to 60 chars), author, branch, age in days

```
## open-source/repo-alpha

| # | PR   | Title                        | Author  | Branch              | Age |
|---|------|------------------------------|---------|---------------------|-----|
| 1 | #142 | Add webhook retry logic      | alice   | webhook-retry       | 12d |
| 2 | #145 | Fix tenant isolation bug     | bob     | fix-tenant-iso      | 3d  |

## open-source/repo-beta

| # | PR   | Title                        | Author  | Branch              | Age |
|---|------|------------------------------|---------|---------------------|-----|
| 3 | #89  | Migrate to Kysely            | carol   | kysely-migration    | 7d  |
```

After displaying, offer: "Pick a number to review, or paste a PR URL."

Also check for stale review state files in `notes/pr-reviews/` (reviews saved but never posted). If found, offer to clean them up or resume.

---

## Review Pipeline

### Step 1: Check for In-Progress Review

Review state is saved to `notes/pr-reviews/{repo}-{pr_number}.md` with YAML frontmatter.

If a saved review exists:
- If `status: posted` -- start fresh
- If `status: findings_ready` or `status: drafting` -- offer to resume or start fresh
- On resume: always re-run context gathering to account for new commits

Track `head_sha` in state so you can detect if the PR has new commits since the review started.

---

### Step 2: Context Gathering (parallel)

Save the current branch before doing anything:
```bash
ORIGINAL_BRANCH=$(git rev-parse --abbrev-ref HEAD)
```

Run all of these in parallel:
- Fetch PR metadata (title, description, author, base/head branch, head SHA) via `gh pr view`
- Fetch changed files with diffs via `gh pr diff`
- Fetch inline review comments via `get_pull_request_comments` MCP tool
- Fetch conversation comments via `gh api repos/{owner}/{repo}/issues/{pr_number}/comments`
  - **Two APIs needed.** Inline comments and conversation comments are separate. Most human feedback lives in conversation comments. Skipping the second call means missing context already discussed.
- **Tab project lookup (optional):** If the Tab for Projects MCP server is available, search `mcp__tab-for-projects__list_projects()` for a project matching the PR title, branch name, or description keywords. If found, load the project's tasks (`list_tasks({ project_id, status: "done" })` and `list_tasks({ project_id, status: "in_progress" })`) to get acceptance criteria. Pass these to the Acceptance QA agent in Step 3. If Tab is not available, skip this step.
- **Jira ticket lookup (optional):** If Jira MCP tools are available, extract a ticket key from the PR title or branch name (e.g., `RAD-1337` from `RAD-1337-fix-login` or `RAD-1337: Fix login`). If found, fetch the ticket summary, description, and acceptance criteria. Pass to the Acceptance QA agent in Step 3.

After metadata returns (provides the branch name), checkout the PR branch:
```bash
gh pr checkout {pr_number}
```

**Show existing comments** to the user before launching review agents so they see what has already been discussed.

**Backport detection:** If the PR targets a release branch (not main/master), this is likely a backport. Check `notes/pr-reviews/` for a prior review of the same work (match by ticket key from PR title or branch name). If found, offer:
- **Skip** -- already reviewed on the original PR
- **Quick diff** -- compare cherry-pick drift only (what changed between the original and backport)
- **Full review** -- treat as new

---

### Step 3: Launch Review Agents (parallel)

Launch 5-7 agents in parallel. Each receives the **full diff inlined in its prompt** so agents do not need to run git commands to find changed code. They CAN read additional files for surrounding context.

**For large diffs (>200KB):** split files across agents by domain instead of duplicating the entire diff to every agent.

#### Agent lineup

1. **Edge Case QA** -- boundary conditions, null handling, race conditions, async edge cases, error paths. Thinks like a breaker.

2. **Acceptance QA** (HIGHEST PRIORITY) -- verify PR description claims match actual code. Trace data flow. Check for `.map()` stale state bugs, `Promise.all()` over shared state, upsert logic that drops fields, tests that only use 1 item per key. Check test coverage of real data shapes. When external context is available (Tab project acceptance criteria, Jira ticket criteria, or both), verify code against those criteria, not just PR claims.

3. **Researcher** -- git blame on modified sections, prior PRs that touched these files, history patterns, TODO/FIXME that should have been addressed. Uses git history, not just the diff.

4. **Code Reviewer** -- CLAUDE.md standards compliance. Read the repo's CLAUDE.md first. Only flags violations of explicitly stated rules. Never invents rules that do not exist.

5. **Code Smells** -- Fowler catalog: long methods, feature envy, data clumps, excessive coupling, primitive obsession, complex conditionals. Skips test files (different design constraints apply).

6. **Test Reviewer** (conditional, only if test files in changeset) -- hollow assertions, over-mocking, bloated permutation tests, AI-generated test smells, mock leak, testing the wiring.

7. **Dynamic Specialists** (conditional, only when relevant):

| Artifact | Trigger | Focus |
|----------|---------|-------|
| Claude/AI skill files | Any SKILL.md or agent definition added/modified | Trigger accuracy, codebase correctness, drift from actual code |
| DB migrations | Any migration file | Schema safety, rollback plan, data loss risk |
| CI/CD config | Any workflow file | Correctness, security, performance |
| Docker/infra | Dockerfile, compose files | Security, layer efficiency, env leaks |

#### Agent output format

Every agent returns structured findings:
```
[file.ts:42] [severity: critical|high|medium|low] Description
-> Suggested fix: ...
```

Plus a `NICE` category for positive observations worth calling out in the blurb.

---

### Step 4: Consolidate Findings

1. Collect all findings from all agents
2. **Deduplicate** findings at the same file:line from different agents (keep the higher severity, merge descriptions)
3. **Sort:** critical > high > medium > low > NICE (positive observations)
4. Present as a numbered table:

```
| #  | Sev      | File            | Line | Agent          | Description                    |
|----|----------|-----------------|------|----------------|--------------------------------|
| 1  | critical | service.ts      | 42   | Edge Case QA   | Unhandled null in upsert       |
| 2  | high     | controller.ts   | 18   | Acceptance QA  | Missing validation on input    |
| 3  | medium   | repository.ts   | 93   | Code Reviewer  | Violates naming rule in CLAUDE |
| 4  | low      | helpers.ts      | 7    | Code Smells    | Feature envy on config object  |
| 5  | NICE     | test/service.ts | --   | Test Reviewer  | Great edge case coverage       |
```

Save findings to `notes/pr-reviews/{repo}-{pr_number}.md` with `status: findings_ready`.

---

### Step 5: Walk Through Findings ONE AT A TIME

Before starting the walk-through, update the review state file status to `drafting`.

**Do NOT batch all findings and ask "which ones do you want?"** Present each finding individually.

For each finding:
1. Show the finding: number, severity, file, line, agent, full description
2. Ask: **comment**, **skip**, or **tweak**?
3. If comment: draft the comment text using the voice rules below. Show the draft.
4. Wait for user approval, edits, or "skip"
5. Move to the next finding

**Why one at a time matters:**
- Some findings should be combined into one comment
- Related findings should cross-reference each other ("Similar theme to the credential table comment")
- Some findings are already covered by another comment's fix
- The user might want to escalate a nit to medium, or downgrade a medium to nit
- Pre-existing issues need authorship context (git blame) before framing

---

### Step 6: Draft the Review Batch

**This step MUST happen in the main context, not a sub-agent.** Voice consistency requires human-in-the-loop drafting.

After walking through all findings, present the complete batch:

**Top-level blurb:**
- 2-3 sentences calling out what the PR does well (specific, not generic)
- Set tone for inline comments: "Left a couple small thoughts inline" or similar
- Praise goes here, not in inline comments (praise-only inline comments are clutter)
- If any findings reference code OUTSIDE the diff, include them here with clickable permalink links

**Approved inline comments** in a table:
```
| # | File:Line          | Comment text (truncated preview)     |
|---|--------------------|--------------------------------------|
| 1 | service.ts:42      | This upsert doesn't handle the ca... |
| 2 | controller.ts:18   | The input validation here misses...  |
```

**Body-only comments** (for lines outside the diff):
- Include GitHub permalink: `https://github.com/{owner}/{repo}/blob/{head_sha}/{path}#L{line}`
- Every finding in the blurb MUST include a clickable link. Never reference "line ~93" without a link.

---

### Step 7: Post After Explicit Approval

**Never post without the user saying "post" or "go."**

Show the full draft one more time. Ask: "Good to post? You can also edit any comment."

If the user wants edits: apply them, re-present, ask again.

After approval, ask: **Approve** this PR, or just leave a **comment**?
- Comment only: `event: COMMENT`
- Approve: `event: APPROVE`

**Use Python for the payload** (shell escaping with markdown is fragile):

```python
import json

payload = {
    'event': 'COMMENT',  # or 'APPROVE'
    'body': '''Top-level blurb text here''',
    'comments': [
        {
            'path': 'path/to/file.ts',
            'line': 42,
            'side': 'RIGHT',
            'body': 'Inline comment text here'
        },
    ]
}

with open('/tmp/pr-review.json', 'w') as f:
    json.dump(payload, f)
```

Then post:
```bash
gh api repos/{owner}/{repo}/pulls/{pr_number}/reviews --method POST --input /tmp/pr-review.json
```

**Line placement rules:**
- If the finding's line is IN the diff: post as inline comment using `line` + `side: "RIGHT"`
- If the finding's line is OUTSIDE the diff: put it in the review body with a clickable permalink
- Do NOT use `position` (deprecated diff-relative counting)
- For new files, the diff position = file line number + 1 (the @@ header is position 1)
- For multi-hunk files, positions count continuously across all hunks. If unsure, put it in the body with a permalink instead of guessing wrong.

Clean up temp files after posting. Update review state to `status: posted`.

---

### Step 8: Restore Original Branch

**This step runs ALWAYS** -- after posting, after a failed post, or if the user skips posting. Never leave the user on the PR branch.

```bash
git checkout {ORIGINAL_BRANCH}
```

---

## Voice and Tone Rules

These rules are non-negotiable. Every comment posted on behalf of the reviewer MUST follow them.

### Tone

- Write like a teammate, not a report generator or a linter
- Lead with the observation. No greetings, no hedging preamble.
- "nit:" prefix already signals low pressure. No need to add disclaimers.
- Frame feedback as observations: "I don't think there's a `direct/` subdirectory" NOT "you should fix this path"
- Contractions are fine and sound more human ("don't", "isn't", "won't")
- "Would it be worth..." is fine for suggestions, but don't overuse hedging language
- When findings relate to each other, cross-reference: "Similar theme to the credential table comment"
- Offer concrete suggestions: code examples, specific alternatives, renamed values
- Don't reference internal standards documents or style guides. Frame as personal observations.

### AI Tells to AVOID

These are dead ringers for AI-generated text. Humans WILL notice.

- **Em dashes**: The #1 AI tell. NEVER use them in comment text. Use periods, commas, or restructure the sentence.
- **"Hey!" openers**: Every AI code review starts with this. Don't.
- **"Just wanted to flag"** / **"Just thinking out loud"** / **"Just a heads up"**: Filler that screams AI.
- **"Not blocking!" / "Totally not blocking"**: If it's a nit, the prefix says it. No disclaimer needed.
- **Walls of text**: Break into short paragraphs. 1-2 sentences each.
- **Lecture-style explanations**: You're commenting, not teaching a class.
- **"you should" / "this needs to"**: Commanding language. Rephrase as observations or questions.
- **No cheesy encouragement**: "Could be a nice boy scout opportunity" sounds terrible.

### Comment Structure

Every comment follows: **(1) what's wrong > (2) why it matters > (3) suggested fix**

Bad:
> Hey! Just wanted to flag that this TODO looks like it might be stale -- the severity mapping was implemented in this PR so the tests should pass. Not blocking, but might be worth removing it so future developers don't get confused by it.

Good:
> This TODO looks stale now. The severity mapping landed in the same PR (`mapAppSecFindingSeverity` reads from `finding.severity`), so these assertions should pass. Might want to just pull this comment out so nobody down the road reads it and assumes these tests are expected to fail.

### Authorship Context

Before commenting on pre-existing issues, **check git blame**:

1. If the PR author also wrote the pre-existing code: "while you're in here" framing is fair game
2. If they did NOT write it: "Not from this PR, but..." framing, suggest as a follow-up
3. Never pressure people to fix other people's messes in their PR

### Grouping and Skipping

- If multiple findings make the same point, comment on the best example and skip the rest
- If a finding is covered by another comment's fix, skip it
- When a PR introduces a pattern, look for a "theme" across findings. Call out the theme once rather than repeating N times.
- Check: would the user miss a finding if you skipped it? If fixing finding A naturally leads to discovering finding B, skip B.

### Top-Level Blurb

- Call out what the PR does well. Be specific, not generic. ("Love that you hit all the case variants" beats "great tests")
- Set the tone: "Left some thoughts below and a couple inline"
- Weave praise here, not in inline comments. Praise-only inline comments are clutter.
- If findings can't be posted inline (outside the diff), put them in the blurb with clickable permalink links

### Never Include

- AI attribution ("Generated with Claude Code" or any variant)
- Inline praise-only comments
- Lecture-style explanations
- Em dashes in running text

### Approval Comments

When approving a PR: body is signature approval emojis only. No other text.

---

## Review State Persistence

Save review state to `notes/pr-reviews/{repo}-{pr_number}.md`:

```yaml
---
repo: owner/repo
pr_number: 142
head_sha: abc123
status: findings_ready  # findings_ready | drafting | posted
reviewed_at: 2026-04-23T14:30:00
original_branch: main
---
```

Below the frontmatter, store the findings table and any approved comment drafts.

**On resume:**
- Re-fetch PR metadata to check for new commits (compare head SHA)
- If new commits since review: warn the user, offer to re-run agents or continue with stale findings
- Restore the findings walk-through from where it left off

---

## Backport Handling

If the PR targets a release branch (not main/master):

1. Detect as backport from the base branch name
2. Search `notes/pr-reviews/` for a prior review of the same ticket (match ticket key from PR title or branch)
3. If prior review found, offer:
   - **Skip** -- code was already reviewed on the original PR
   - **Quick diff** -- compare cherry-pick drift only (what changed between original and backport)
   - **Full review** -- treat as new, run the complete agent pipeline

Most backports should be "quick diff" to verify the cherry-pick is clean and no new code was added.

---

## Integrations

The review pipeline auto-detects available integrations. No configuration needed.

| Integration | Detection | What it adds to reviews |
|-------------|-----------|------------------------|
| **GitHub** | Always available (uses `gh` CLI) | PR metadata, diffs, comments, review posting |
| **Tab for Projects** | `mcp__tab-for-projects__list_projects` responds | Acceptance criteria from matching Tab project tasks |
| **Jira** | Jira MCP tools available (e.g., `mcp__jira__get_issue`) | Ticket summary, description, acceptance criteria, bug repro steps |

When multiple integrations are available, the Acceptance QA agent receives context from all of them. The more context it has, the stronger its verification.

If none of the optional integrations are available, the review still works. The Acceptance QA agent verifies PR description claims against the actual code.

---

## Quick Reference

### GitHub API calls used

```bash
# PR metadata
gh pr view {url_or_number} --json title,body,author,baseRefName,headRefName,headRefOid,number,url,state

# PR diff
gh pr diff {url_or_number}

# PR changed files
gh pr diff {url_or_number} --name-only

# Conversation comments (different from inline comments!)
gh api repos/{owner}/{repo}/issues/{pr_number}/comments

# Post review batch
gh api repos/{owner}/{repo}/pulls/{pr_number}/reviews --method POST --input /tmp/pr-review.json

# Checkout PR branch
gh pr checkout {pr_number}
```

### MCP tools used

```
mcp__github__get_pull_request_comments  -- inline review comments
mcp__github__get_pull_request           -- PR metadata (alternative to gh cli)
mcp__github__get_pull_request_files     -- changed files list
```
