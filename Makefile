.PHONY: build
build: build-frontend build-backend

.PHONY: build-frontend
build-frontend:
	docker build -t python-blockchain-frontend -f Dockerfile.frontend .

.PHONY: build-backend
build-backend:
	docker build -t python-blockchain-backend -f Dockerfile.backend .
