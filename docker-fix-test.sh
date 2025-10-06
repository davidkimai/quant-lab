#!/usr/bin/env bash
# Docker Fix Verification & Testing Script

set -e

echo "======================================================================"
echo "DOCKER BUILD FIX - VERIFICATION & TESTING"
echo "======================================================================"
echo ""

cd /home/claude/quant-lab

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "Problem Diagnosed:"
echo "  • Docker build context was set to ./packages/api"
echo "  • Dockerfile tried to COPY ../core (outside build context)"
echo "  • Result: '/core': not found error"
echo ""

echo "Fixes Applied:"
echo "  ✓ Changed build context to repository root (.)"
echo "  ✓ Updated API Dockerfile paths (packages/core, packages/api)"
echo "  ✓ Updated Web Dockerfile paths (packages/web/)"
echo "  ✓ Removed problematic volume mounts"
echo "  ✓ Added .dockerignore for optimized builds"
echo ""

echo "======================================================================"
echo "STEP 1: Verify Docker Configuration"
echo "======================================================================"
echo ""

echo "[1.1] Checking docker-compose.yml build contexts..."
if grep -q "context: \." docker-compose.yml && grep -q "dockerfile: ./packages/api/Dockerfile" docker-compose.yml; then
    echo -e "  ${GREEN}✓${NC} API build context: root directory"
else
    echo -e "  ${RED}✗${NC} API build context incorrect"
    exit 1
fi

if grep -q "context: \." docker-compose.yml && grep -q "dockerfile: ./packages/web/Dockerfile" docker-compose.yml; then
    echo -e "  ${GREEN}✓${NC} Web build context: root directory"
else
    echo -e "  ${RED}✗${NC} Web build context incorrect"
    exit 1
fi

echo ""
echo "[1.2] Checking Dockerfile paths..."
if grep -q "COPY packages/core /app/core" packages/api/Dockerfile; then
    echo -e "  ${GREEN}✓${NC} API Dockerfile uses correct core path"
else
    echo -e "  ${RED}✗${NC} API Dockerfile path incorrect"
    exit 1
fi

if grep -q "COPY packages/api /app/api" packages/api/Dockerfile; then
    echo -e "  ${GREEN}✓${NC} API Dockerfile uses correct api path"
else
    echo -e "  ${RED}✗${NC} API Dockerfile path incorrect"
    exit 1
fi

if grep -q "COPY packages/web/" packages/web/Dockerfile; then
    echo -e "  ${GREEN}✓${NC} Web Dockerfile uses correct web path"
else
    echo -e "  ${RED}✗${NC} Web Dockerfile path incorrect"
    exit 1
fi

echo ""
echo "[1.3] Verifying directory structure..."
for dir in "packages/core" "packages/api" "packages/web"; do
    if [ -d "$dir" ]; then
        echo -e "  ${GREEN}✓${NC} $dir exists"
    else
        echo -e "  ${RED}✗${NC} $dir not found"
        exit 1
    fi
done

echo ""
echo "[1.4] Checking .dockerignore..."
if [ -f ".dockerignore" ]; then
    echo -e "  ${GREEN}✓${NC} .dockerignore exists (optimizes builds)"
else
    echo -e "  ${YELLOW}⚠${NC} .dockerignore not found (non-critical)"
fi

echo ""
echo -e "${GREEN}All configuration checks passed!${NC}"
echo ""

echo "======================================================================"
echo "STEP 2: Clean Previous Docker State"
echo "======================================================================"
echo ""

echo "Stopping any running containers..."
docker-compose down 2>/dev/null || true

echo ""
echo "Removing previous images (if any)..."
docker-compose rm -f 2>/dev/null || true
docker images | grep quant-lab | awk '{print $3}' | xargs -r docker rmi -f 2>/dev/null || true

echo ""
echo -e "${GREEN}✓${NC} Previous Docker state cleaned"
echo ""

echo "======================================================================"
echo "STEP 3: Test Docker Build (API Service)"
echo "======================================================================"
echo ""

echo "Building API service..."
echo "(This will take 1-2 minutes on first build)"
echo ""

if docker-compose build api; then
    echo ""
    echo -e "${GREEN}✓✓✓ API BUILD SUCCESSFUL! ✓✓✓${NC}"
    echo ""
else
    echo ""
    echo -e "${RED}✗✗✗ API BUILD FAILED ✗✗✗${NC}"
    echo ""
    echo "Debug Information:"
    echo "  • Check that packages/core and packages/api exist"
    echo "  • Verify Python dependencies are available"
    echo "  • Look for any COPY errors in the output above"
    echo ""
    exit 1
fi

echo "======================================================================"
echo "STEP 4: Test Docker Build (Web Service)"
echo "======================================================================"
echo ""

echo "Building Web service..."
echo "(This will take 1-2 minutes on first build)"
echo ""

if docker-compose build web; then
    echo ""
    echo -e "${GREEN}✓✓✓ WEB BUILD SUCCESSFUL! ✓✓✓${NC}"
    echo ""
else
    echo ""
    echo -e "${RED}✗✗✗ WEB BUILD FAILED ✗✗✗${NC}"
    echo ""
    echo "Debug Information:"
    echo "  • Check that packages/web exists"
    echo "  • Verify package.json and package-lock.json are present"
    echo "  • Look for npm errors in the output above"
    echo ""
    exit 1
fi

echo "======================================================================"
echo "STEP 5: Start Full Stack"
echo "======================================================================"
echo ""

echo "Starting all services (postgres, api, web)..."
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop services when done testing${NC}"
echo ""

docker-compose up

# This will be reached when user stops with Ctrl+C
echo ""
echo "======================================================================"
echo "SERVICES STOPPED"
echo "======================================================================"
