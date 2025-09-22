# Database Port Change Summary

## 🔄 Port Changed: 5432 → 5433

The local PostgreSQL database port has been changed from **5432** to **5433** to avoid conflicts with your other project.

## 📝 Files Updated

### Docker Configuration
- `docker-compose.yml` - Changed port mapping to `5433:5432`
- `docker-compose.email.yml` - Changed port mapping to `5433:5432`

### Environment Files
- `railway.env.example` - Updated localhost connection to port 5433

### Scripts
- `setup.sh` - Updated port conflict checking and DB_PORT variable
- `quick-fix.sh` - Updated port killing to target 5433

### Documentation
- `chicken_management_date.md` - Updated port references

### New Files
- `connect-db.sh` - Helper script to connect to database on port 5433

## 🚀 How to Use

### Start the Project
```bash
# Start with Docker Compose
docker-compose up -d

# Or use the setup script
./setup.sh
```

### Connect to Database
```bash
# Using the helper script
./connect-db.sh

# Or manually
psql -h localhost -p 5433 -U postgres -d chicken_management
```

### Database Connection Details
- **Host**: localhost
- **Port**: 5433 (changed from 5432)
- **Database**: chicken_management
- **User**: postgres
- **Password**: password

## ✅ Benefits

1. **No Port Conflicts** - Won't clash with your other project using port 5432
2. **Easy Switching** - Can run both projects simultaneously
3. **Clear Separation** - Each project has its own database port
4. **Helper Scripts** - Easy database connection and management

## 🔧 Internal Docker Communication

**Important**: The internal Docker communication still uses port 5432. Only the external port mapping changed:
- **External Access**: localhost:5433
- **Internal Docker**: db:5432 (unchanged)
- **DATABASE_URL**: Still uses `db:5432` internally

This means your Django backend will continue to work without any changes to the internal configuration.
