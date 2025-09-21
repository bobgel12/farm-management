# Cursor AI Development Setup

This document describes the complete development setup for the Chicken House Management system using Cursor AI.

## 🚀 Quick Start

1. **Open in Cursor**: Open this project in Cursor AI
2. **Install dependencies**: Run `./scripts/dev-setup.sh`
3. **Start development**: Run `./scripts/start-dev.sh`
4. **Access application**: 
   - Frontend: http://localhost:3000
   - Backend: http://localhost:8000
   - Admin: http://localhost:8000/admin

## 📁 Project Structure

```
chicken_house_management/
├── .cursorrules              # Cursor AI rules and instructions
├── .cursorignore            # Files to ignore in Cursor
├── .vscode/                 # VS Code/Cursor configuration
│   ├── settings.json        # Editor settings
│   ├── extensions.json      # Recommended extensions
│   ├── tasks.json          # Development tasks
│   └── launch.json         # Debug configurations
├── scripts/                 # Development scripts
│   ├── dev-setup.sh        # Initial setup
│   ├── start-dev.sh        # Start development servers
│   ├── lint-check.sh       # Code quality checks
│   └── fix-code.sh         # Auto-fix code issues
├── backend/                 # Django backend
│   ├── pyproject.toml      # Python tooling config
│   └── ...
├── frontend/               # React frontend
│   ├── .eslintrc.js        # ESLint configuration
│   ├── .prettierrc         # Prettier configuration
│   ├── tsconfig.json       # TypeScript configuration
│   └── ...
└── docs/                   # Documentation
```

## 🛠️ Development Tools

### Code Quality
- **ESLint**: JavaScript/TypeScript linting
- **Prettier**: Code formatting
- **Black**: Python code formatting
- **isort**: Python import sorting
- **Flake8**: Python linting
- **MyPy**: Python type checking

### Editor Configuration
- **Auto-format on save**: Enabled
- **Auto-fix on save**: Enabled
- **TypeScript support**: Full IntelliSense
- **Python support**: Django-aware
- **Import organization**: Automatic

### Scripts
- `./scripts/dev-setup.sh`: Complete development setup
- `./scripts/start-dev.sh`: Start both servers
- `./scripts/lint-check.sh`: Run all quality checks
- `./scripts/fix-code.sh`: Auto-fix common issues

## 🎯 Cursor AI Features

### Code Generation
Cursor AI is configured to understand:
- Django REST Framework patterns
- React TypeScript best practices
- Material-UI component usage
- API integration patterns
- Authentication flows
- Database models and serializers

### Context Awareness
The `.cursorrules` file provides:
- Project-specific coding standards
- Architecture patterns
- Security guidelines
- Performance considerations
- Testing requirements

### Auto-completion
Enhanced with:
- TypeScript type definitions
- Django model fields
- React component props
- API endpoint patterns
- Error handling patterns

## 🔧 Configuration Files

### .cursorrules
Contains comprehensive instructions for:
- Code style and standards
- Architecture patterns
- Security guidelines
- Testing requirements
- Git workflow
- Common patterns and examples

### .vscode/settings.json
Editor configuration for:
- Format on save
- Lint on save
- TypeScript settings
- Python settings
- File associations
- Search exclusions

### .vscode/tasks.json
Pre-configured tasks for:
- Starting servers
- Running tests
- Linting code
- Building projects
- Docker operations

### .vscode/launch.json
Debug configurations for:
- Django development server
- React development server
- Test runners
- Full-stack debugging

## 🚦 Development Workflow

### 1. Initial Setup
```bash
# Clone repository
git clone <repository-url>
cd chicken_house_management

# Run setup script
./scripts/dev-setup.sh

# Start development
./scripts/start-dev.sh
```

### 2. Daily Development
```bash
# Start development servers
./scripts/start-dev.sh

# In another terminal, run quality checks
./scripts/lint-check.sh

# Fix code issues automatically
./scripts/fix-code.sh
```

### 3. Code Quality
- **Automatic**: Format on save, lint on save
- **Manual**: Run `./scripts/lint-check.sh`
- **Fix**: Run `./scripts/fix-code.sh`

### 4. Testing
- **Frontend**: `cd frontend && npm test`
- **Backend**: `cd backend && python manage.py test`

## 🎨 Code Style

### TypeScript/React
- Use functional components with hooks
- Prefer arrow functions
- Use TypeScript strict mode
- Follow Material-UI patterns
- Implement proper error boundaries

### Python/Django
- Follow PEP 8 style
- Use Django REST Framework patterns
- Write comprehensive docstrings
- Use type hints where possible
- Follow Django best practices

## 🔍 Debugging

### Frontend Debugging
- Use React Developer Tools
- Set breakpoints in VS Code
- Use browser dev tools
- Check network requests

### Backend Debugging
- Use Django debug toolbar
- Set breakpoints in VS Code
- Use Django shell for testing
- Check logs in `backend/logs/`

### Full-Stack Debugging
- Use compound launch configuration
- Debug both frontend and backend simultaneously
- Use network tab to trace API calls

## 📚 Learning Resources

### Cursor AI
- [Cursor Documentation](https://cursor.sh/docs)
- [Cursor AI Features](https://cursor.sh/features)
- [Best Practices](https://cursor.sh/docs/best-practices)

### Project-Specific
- [Django REST Framework](https://www.django-rest-framework.org/)
- [React TypeScript](https://react-typescript-cheatsheet.netlify.app/)
- [Material-UI](https://mui.com/)

## 🐛 Troubleshooting

### Common Issues

1. **Port conflicts**:
   ```bash
   # Kill processes on ports
   lsof -ti:3000 | xargs kill -9
   lsof -ti:8000 | xargs kill -9
   ```

2. **Dependencies issues**:
   ```bash
   # Frontend
   cd frontend && rm -rf node_modules && npm install
   
   # Backend
   cd backend && rm -rf venv && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt
   ```

3. **Database issues**:
   ```bash
   cd backend
   source venv/bin/activate
   python manage.py makemigrations
   python manage.py migrate
   ```

### Getting Help
1. Check the troubleshooting section in `DEVELOPMENT.md`
2. Run `./scripts/lint-check.sh` to identify issues
3. Use Cursor AI chat for specific questions
4. Check existing issues in the repository

## 🎉 Success!

You now have a fully configured development environment with:
- ✅ Cursor AI integration
- ✅ Code quality tools
- ✅ Development scripts
- ✅ Debug configurations
- ✅ TypeScript support
- ✅ Python/Django support
- ✅ Comprehensive documentation

Happy coding! 🚀
