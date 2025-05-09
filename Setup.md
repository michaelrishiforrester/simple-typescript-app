# Setup Guide for Simple TypeScript App

## Prerequisites

- Node.js (v20.0.0 or higher)
- npm (comes with Node.js)
- Git (for version control)

## Local Development Setup

1. **Clone the repository**

   ```bash
   git clone <repository-url>
   cd simple-typescript-app
   ```

2. **Install dependencies**

   ```bash
   npm install
   ```

3. **Build the application**

   ```bash
   npm run build
   ```

4. **Run the application**

   ```bash
   npm run dev
   ```

   The application will be available at http://localhost:3000

## Docker Setup

1. **Build the Docker image**

   ```bash
   docker build -t simple-typescript-app .
   ```

2. **Run the Docker container**

   ```bash
   docker run -p 3000:3000 simple-typescript-app
   ```

   The application will be available at http://localhost:3000

## AWS Deployment

### Prerequisites

- AWS CLI configured with appropriate permissions
- AWS CodeDeploy agent installed on target EC2 instances

### Deployment Steps

1. **Create an S3 bucket for deployment artifacts**

   ```bash
   aws s3 mb s3://your-deployment-bucket
   ```

2. **Create a deployment**

   ```bash
   aws deploy create-deployment \
     --application-name simple-typescript-app \
     --deployment-group-name production \
     --revision "revisionType=S3,s3Location={bucket=your-deployment-bucket,key=simple-typescript-app.zip,bundleType=zip}" \
     --description "Deployment via CLI"
   ```

## Environment Variables

- `PORT`: The port the application will listen on (default: 3000)
- `NODE_ENV`: The environment the application is running in (development, production)

## Running Tests

```bash
npm run lint
```

## Security Checks

```bash
npm run security-check
```

## Troubleshooting

### Common Issues

1. **Port already in use**
   
   If port 3000 is already in use, you can change the port by setting the PORT environment variable:
   
   ```bash
   PORT=3001 npm run dev
   ```

2. **Build errors**
   
   If you encounter build errors, try cleaning the build artifacts:
   
   ```bash
   rm -rf dist
   npm run build
   ```

3. **Dependency issues**
   
   If you encounter dependency issues, try reinstalling the dependencies:
   
   ```bash
   rm -rf node_modules
   npm install
   ```