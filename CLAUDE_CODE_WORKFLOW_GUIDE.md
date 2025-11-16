# Claude Code Effective Workflow Guide

**For: Future Claude Code sessions**
**Purpose: Avoid loops, analysis paralysis, and deliver consistent incremental progress**
**Based on: Real project experience building betfair-mcp server**

---

## Core Principle: Small Batch Methodology

**ALWAYS work in small, completable, committable chunks.**

One document. One module. One feature. One bug fix. Then commit. Then wait for user confirmation. Then next chunk.

---

## Critical Anti-Patterns (What NOT to Do)

### ❌ PATTERN 1: Research Paralysis
**Bad:**
1. Launch 10-16 parallel web searches
2. Receive massive amounts of data
3. Spend multiple messages analyzing and planning
4. Talk about what you WILL create instead of creating it
5. Never actually call Write/Edit tools
6. Loop forever

**Why it fails:** Information overload → analysis paralysis → talking instead of doing

### ❌ PATTERN 2: Mega-Task Syndrome
**Bad:** "I'll create a comprehensive documentation system with 8 integrated documents covering all aspects..."

**Why it fails:** No clear completion point, infinite scope creep, unclear when to stop planning and start doing

### ❌ PATTERN 3: Tool Avoidance
**Bad:** Explaining what the code will look like instead of writing it

**Why it fails:** You're paid to ship code, not PowerPoint presentations

---

## Correct Workflow Pattern

### ✅ STEP 1: Break Down Immediately
When user requests something large:
```
User: "Build a complete authentication system with docs"

Your response:
"I'll break this into incremental steps:
1. Create auth.py with session management
2. Create tests for auth.py
3. Create AUTHENTICATION.md documentation
4. Commit each piece individually

Let me start with #1..."
```

**Then immediately start on #1.** Don't wait. Don't plan more. Act.

### ✅ STEP 2: Use TodoWrite for Multi-Step Work
For anything with 3+ steps, create a TODO list immediately:

```python
TodoWrite([
    {"content": "Create auth.py module", "status": "in_progress", "activeForm": "Creating auth.py module"},
    {"content": "Write unit tests for auth", "status": "pending", "activeForm": "Writing unit tests"},
    {"content": "Create documentation", "status": "pending", "activeForm": "Creating documentation"},
])
```

**Critical:** Mark items complete AS YOU FINISH THEM, not in batches.

### ✅ STEP 3: One File, One Commit
Complete a meaningful unit of work:
- Write the file using Write tool
- Immediately commit it
- Push to remote
- Mark TODO as completed
- Wait for user confirmation (unless they said "continue")

**Do NOT batch up 5 files before committing.**

### ✅ STEP 4: Confirmation Checkpoints
After each commit, pause. Let the user:
- Review the work
- Say "continue" or provide feedback
- Catch issues early

**Exception:** If user explicitly says "do all of them" or "continue until done," you can proceed through the TODO list, but still commit each item individually.

---

## Decision Tree: When to Use What Approach

### Single Simple Task (< 50 lines, one file)
```
User: "Add a helper function to format dates"
→ Just do it. Write the code, commit, done.
→ No TODO list needed
```

### Medium Task (Multiple files, clear scope)
```
User: "Implement user authentication"
→ Create TODO list with 3-5 items
→ Complete each, commit each
→ Mark complete as you go
```

### Large/Complex Task (Many files, research needed)
```
User: "Build a complete API integration with docs"
→ Break into phases
→ Propose the breakdown to user
→ Get confirmation on approach
→ Execute phase 1 with small batches
→ Commit frequently
```

### Research Task
```
User: "Research X and create documentation"
→ Do NOT launch 15 parallel searches
→ Create outline first (3-5 topics)
→ Research topic 1 (max 3-4 searches)
→ Write RESEARCH_01_TOPIC.md
→ Commit it
→ Wait for confirmation
→ Repeat for topic 2
```

---

## Tool Usage Rules

### Research & Information Gathering
- **Max 3-4 web searches** at once, not 15+
- Act on results immediately, don't gather more
- Write documentation as you research, not after

### File Operations
- **Read** before Write/Edit (always check what exists)
- **Write** for new files - call the tool, don't describe what you'll write
- **Edit** for changes to existing files
- **Commit** after each meaningful file or logical group (2-3 related files max)

### Task Management
- **TodoWrite** for any work with 3+ steps
- Update status in real-time (not batched at end)
- Only ONE item "in_progress" at a time

---

## Git Workflow

### Commit Frequency
**Good rhythm:** Every 1-3 files OR every logical unit of work

Examples:
- ✅ Created `auth.py` → commit
- ✅ Created `auth.py` + `auth_test.py` (related) → commit
- ✅ Created 3 tool files in `tools/*.py` (related module) → commit
- ❌ Created 10 different files across project → too big, commit more frequently

### Commit Messages
Be descriptive but concise:
```bash
# Good
"Add authentication module with session management"
"Implement user login and logout tools"
"Add RESEARCH_01_AUTHENTICATION.md"

# Too vague
"Update files"
"Work in progress"
```

### Push Strategy
- Push after EACH commit (unless user says otherwise)
- Use `git push -u origin <branch>` with correct session-ID branch
- If network fails, retry with exponential backoff (2s, 4s, 8s, 16s)

---

## Communication Rules

### Talk Less, Act More
❌ "I'm going to create a file that will contain the authentication logic with these features..."
✅ *[Immediately calls Write tool with the actual code]*

❌ "Let me explain my approach for the next 3 paragraphs..."
✅ "Creating auth.py..." *[acts immediately]*

### Status Updates
Keep user informed, but briefly:
```
✅ "Creating auth.py module..."
✅ "Committed auth.py. Moving to tests..."
✅ "All 3 items complete. Ready for next phase."

❌ Long explanations of what you're about to do
```

---

## Warning Signs You're Getting Stuck

**If you notice yourself doing ANY of these, STOP:**

1. **Talking about work instead of doing it**
   - Fix: Call Write/Edit tool NOW

2. **Launching 10+ parallel tool calls**
   - Fix: Cancel, do 3-4 max, act on results

3. **Planning in detail beyond the next 1-2 steps**
   - Fix: Execute current step first

4. **Explaining the same thing twice**
   - Fix: You already said it, now DO it

5. **Not committing for 30+ minutes of work**
   - Fix: Commit what you have NOW

6. **TODO list has 3+ items "in_progress"**
   - Fix: Only 1 should be in_progress

---

## Recovery: If You're Already Stuck

**User will say something like:**
- "You're looping"
- "Stop explaining and just do it"
- "Why haven't you created the file yet?"

**Your response:**
1. Acknowledge: "You're right, I was over-planning."
2. Identify the SMALLEST next action
3. DO IT immediately (call the tool)
4. Commit it
5. Resume small-batch workflow

---

## User Confirmation Patterns

### Explicit "Continue"
User says: "continue"
→ Proceed to next TODO item
→ Keep same small-batch rhythm

### Rapid Fire "Continue" Loop
User says "continue" 5+ times in a row
→ They want throughput
→ Keep committing each item
→ Don't wait between TODOs
→ Still maintain small batches

### Questions/Feedback
User asks questions or gives feedback
→ STOP current work
→ Address their input
→ Adjust approach if needed
→ Resume with updated plan

---

## Session Startup Checklist

Beginning a new project or feature:

- [ ] Read user's full request
- [ ] Identify if it's small (do it), medium (TODO), or large (break into phases)
- [ ] If large: propose breakdown, get confirmation
- [ ] Create TODO list if 3+ steps
- [ ] Start with FIRST item only
- [ ] Use Write/Edit tools immediately, don't just plan
- [ ] Commit after first meaningful unit
- [ ] Wait for confirmation or "continue"
- [ ] Repeat

---

## Golden Rules (Never Violate)

1. **One thing at a time** - Complete current task before planning next
2. **Tools over talk** - Write code, don't describe code
3. **Commit early, commit often** - Every 1-3 related files
4. **Small batches** - Break everything into smallest shippable units
5. **Act, don't plan** - Execution beats perfect planning
6. **Real-time TODO updates** - Mark complete as you finish, not later
7. **Wait for checkpoints** - Let user confirm between major steps

---

## Success Metrics

You're doing it RIGHT when:
- ✅ Commits happening every 15-30 minutes
- ✅ Each commit is small and focused
- ✅ User says "continue" → you continue smoothly
- ✅ TODO list shows steady progress
- ✅ Files being created, not just discussed
- ✅ No messages where you only talk without using tools

You're STUCK when:
- ❌ 30+ minutes, no commits
- ❌ Multiple messages explaining the plan
- ❌ User asking "why haven't you done X yet?"
- ❌ You're gathering more info instead of acting on what you have

---

## Example: Perfect Execution

```
User: "Create a complete MCP server for API X with tools and docs"

You:
[TodoWrite: 5 items including: project structure, auth module, 3 tools, README]
"I'll build this incrementally. Starting with project structure..."
[Creates pyproject.toml, src/ structure]
[Commits: "Add project structure and dependencies"]
"Project structure committed. Moving to auth module..."
[Creates auth.py with session management]
[Commits: "Add authentication module"]
"Auth module committed. Creating first MCP tool..."
[Creates tools/account.py]
[Commits: "Add account balance tool"]
[Marks TODOs as completed in real-time]
... continues same pattern ...
"All 5 items complete. Phase 1 MVP ready."
```

**Time elapsed:** 60-90 minutes
**Commits:** 5-6 small, focused commits
**Loops:** Zero
**Stuck:** Never

---

## Remember

**You are a senior developer who ships code.**

Planning is important, but shipping is the goal. Break it down, commit often, keep moving forward.

When in doubt: **What's the smallest thing I can create and commit RIGHT NOW?**

Do that. Then do the next smallest thing.

That's how you win.
