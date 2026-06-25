// Jenkins pipeline for scryme. Mirrors the pantrie project's Kubernetes-pod approach but
// is Python-only: a python container runs the tests against a postgres sidecar, and a glibc
// node container runs the SonarQube scanner (the JS/TS analyzer bridge requires glibc).
pipeline {
    agent {
        kubernetes {
            yaml '''
apiVersion: v1
kind: Pod
spec:
  containers:
    - name: python
      image: python:3.12
      command: ["cat"]
      tty: true
    - name: node
      image: node:20
      command: ["cat"]
      tty: true
    - name: postgres
      image: postgres:16-alpine
      env:
        - name: POSTGRES_USER
          value: scryme
        - name: POSTGRES_PASSWORD
          value: scryme
        - name: POSTGRES_DB
          value: scryme_test
'''
        }
    }

    options {
        timeout(time: 30, unit: 'MINUTES')
    }

    environment {
        SCRYME_DATABASE_URL = 'postgresql+asyncpg://scryme:scryme@localhost:5432/scryme_test'
    }

    stages {
        stage('Backend tests + coverage') {
            steps {
                container('python') {
                    dir('backend') {
                        sh '''
                            python -m venv .venv
                            . .venv/bin/activate
                            pip install --quiet -r requirements-dev.txt

                            echo "Waiting for postgres..."
                            until pg_isready -h localhost -U scryme -d scryme_test 2>/dev/null; do
                                sleep 1
                            done || true
                            python - <<'PY'
import socket, time
for _ in range(60):
    try:
        socket.create_connection(("localhost", 5432), timeout=1).close()
        break
    except OSError:
        time.sleep(1)
PY
                            ruff check src tests
                            pytest tests/
                        '''
                    }
                }
            }
        }

        stage('SonarQube analysis') {
            steps {
                container('node') {
                    withSonarQubeEnv('SonarQube') {
                        sh 'npx --yes @sonar/scan'
                    }
                }
            }
        }

        stage('Quality Gate') {
            steps {
                timeout(time: 5, unit: 'MINUTES') {
                    waitForQualityGate abortPipeline: true
                }
            }
        }
    }
}
