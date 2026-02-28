#!/bin/bash

# SmartPesa - Status Check Script

echo "╔════════════════════════════════════════════════════════════╗"
echo "║     📊 SMART PESA - STATUS CHECK                          ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Check Backend
echo -e "${BLUE}📡 Backend (port 8000):${NC}"
if lsof -i :8000 > /dev/null 2>&1; then
    PID=$(lsof -ti :8000)
    echo -e "  ${GREEN}✅ RUNNING${NC} (PID: $PID)"
else
    echo -e "  ${RED}❌ NOT RUNNING${NC}"
fi
echo ""

# Check Frontend
echo -e "${BLUE}🖥️  Frontend (port 3000):${NC}"
if lsof -i :3000 > /dev/null 2>&1; then
    PID=$(lsof -ti :3000)
    echo -e "  ${GREEN}✅ RUNNING${NC} (PID: $PID)"
else
    echo -e "  ${RED}❌ NOT RUNNING${NC}"
fi
echo ""

# Check Database
echo -e "${BLUE}💾 Database:${NC}"
if [ -f "data/smartpesa.db" ]; then
    SIZE=$(du -h data/smartpesa.db | cut -f1)
    echo -e "  ${GREEN}✅ FOUND${NC} (size: $SIZE)"
else
    echo -e "  ${RED}❌ NOT FOUND${NC}"
fi
echo ""

# Check API Health
echo -e "${BLUE}🌐 API Health:${NC}"
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "  ${GREEN}✅ RESPONDING${NC}"
else
    echo -e "  ${RED}❌ NOT RESPONDING${NC}"
fi
echo ""

echo "╚════════════════════════════════════════════════════════════╝"
