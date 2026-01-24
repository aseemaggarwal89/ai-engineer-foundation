# VS Code – Build & Run Configuration for FastAPI

This document explains **which files to create in VS Code** so you can:
- Run the backend with one click
- Debug without typing commands
- Avoid remembering CLI commands

This is the **VS Code equivalent of npm scripts / nodemon setup**.

---

## 1️⃣ VS Code Tasks (Build / Run Commands)

Create the file:
```
.vscode/tasks.json
```

### Example `tasks.json`
```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "Run FastAPI (dev)",
      "type": "shell",
      "command": "uvicorn app.main:app --reload",
      "group": {
        "kind": "build",
        "isDefault": true
      },
      "problemMatcher": []
    },
    {
      "label": "Run Tests",
      "type": "shell",
      "command": "pytest",
      "group": "test",
      "problemMatcher": []
    },
    {
      "label": "Run Alembic Migrations",
      "type": "shell",
      "command": "alembic upgrade head",
      "problemMatcher": []
    }
  ]
}
```

### How to Use
- `Cmd + Shift + B` → runs **FastAPI dev server**
- Terminal → `Run Task` → choose task

---

## 2️⃣ VS Code Debug Configuration (Recommended)

Create the file:
```
.vscode/launch.json
```

### Example `launch.json`
```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Debug FastAPI",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": [
        "app.main:app",
        "--reload"
      ],
      "jinja": true
    }
  ]
}
```

### How to Use
- Open **Run & Debug** panel
- Click ▶ **Debug FastAPI**
- Set breakpoints anywhere

This is the **best developer experience**.

---

## 3️⃣ Environment Variables (Optional but Clean)

Create:
```
.env
```

Example:
```env
ENV=development
DATABASE_URL=postgresql+asyncpg://user:pass@localhost/db
JWT_SECRET=dev-secret
```

VS Code will auto-load this if Python extension is installed.

---

## 4️⃣ Recommended Folder Structure

```
.vscode/
  ├── tasks.json
  └── launch.json
app/
.env
```

---

## 5️⃣ When to Use What

| Need | Use |
|----|----|
| Quick run | Tasks (`Cmd+Shift+B`) |
| Debug logic | Debug config |
| CI/CD | CLI commands |

---

## ✅ Recommendation

- Use **tasks.json** for daily dev
- Use **launch.json** for debugging
- Keep CLI commands in your cheat sheet

This setup supports **Layer 1 → Layer 9**, including future **AI & RAG** work.

