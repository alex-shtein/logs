#!/bin/bash

# Note: script is expected to be run from root directory during the pipeline

echo 'Running acceptance tests...'

tag=$CI_PROJECT_NAME-$CI_COMMIT_SHA
echo "Building Docker image logs-app:$tag"
docker build --target app . -q -t logs-app:$tag

testNumber=0
failedTests=0

function assertExitCode {
  RED='\033[0;31m'
  GREEN='\033[0;32m'
  NC='\033[0m'

  echo "Exit code: expected=$1, actual=$2"
  if [ $1 -ne $2 ]; then
     echo -e "${RED}Test №${testNumber} failed${NC}"
     failedTests=$((failedTests+1))
  else
     echo -e "${GREEN}Test №${testNumber} passed${NC}"
  fi
}

function assertJsonEquals {
  echo "Comparing JSON's..."
  diff <(docker run --rm -i ghcr.io/jqlang/jq:latest --sort-keys < $1) <(docker run --rm -i ghcr.io/jqlang/jq:latest --sort-keys < $2)
  exit_code=$?
  assertExitCode 0 $exit_code
}

function verifyAllTestsPassed {
  RED='\033[0;31m'
  GREEN='\033[0;32m'
  NC='\033[0m'

  echo "Total failed tests: ${failedTests}"
  if [ $failedTests -ne 0 ]; then
     echo -e "${RED}Some tests have failed!${NC}"
     exit 1
  else
     echo -e "${GREEN}All tests passed${NC}"
     exit 0
  fi
}


function runTest {
  echo "Test [№${testNumber}][$1]: $2; expected exit code: $3; args: ${@:4};"

  docker run --rm \
    -v "$(pwd)/scripts/data:/tmp/data" \
    -v "$(pwd)/scripts/data/input:/tmp/input:ro" \
    logs-app:$tag \
    "${@:4}"

  exit_code=$?
  assertExitCode $3 $exit_code
  testNumber=$((testNumber+1))
}



echo "Running negative tests..."

runTest "negative" "input file does not exist" 2 \
  -p /tmp/input/nonexistent.txt -f json -o /tmp/data/output/output1.json

runTest "negative" "input file has unsupported extension" 2 \
  -p /tmp/inpit/file1.log -f json -o /tmp/data/output/output2.json

runTest "negative" "output file already exists" 2 \
  -p /tmp/inpit/file2.txt -f json -o /tmp/data/output/existing.json

runTest "negative" "output file has unsupported extension (JSON)" 2 \
  -p /tmp/inpit/file2.txt -f json -o /tmp/data/output/output4.txt

runTest "negative" "output file has unsupported extension (MD)" 2 \
  -p /tmp/inpit/file2.txt -f markdown -o /tmp/data/output/output5.txt

runTest "negative" "output file has unsupported extension (AD)" 2 \
  -p /tmp/inpit/file2.txt -f adoc -o /tmp/data/output/output6.txt

runTest "negative" "unsupported output format" 2 \
  -p /tmp/inpit/file2.txt -f txt -o /tmp/data/output/output7.txt

runTest "negative" "invalid date format (--from)" 2 \
  -p /tmp/inpit/file2.txt -f txt -o /tmp/data/output/output8.json --from="2025.01.02"

runTest "negative" "invalid date format (--to)" 2 \
  -p /tmp/inpit/file2.txt -f txt -o /tmp/data/output/output9.json --to="2025.01.02"

runTest "negative" "--from > --to" 2 \
  -p /tmp/inpit/file2.txt -f txt -o /tmp/data/output/output10.json --from="2025-01-02" --to="2025-01-01"

runTest "negative" "required parameter -p is missing" 2 \
  -f json -o /tmp/data/output/output11.json

runTest "negative" "required parameter -f is missing" 2 \
  -p /tmp/input/nonexistent.txt -o /tmp/data/output/output12.json

runTest "negative" "required parameter -o is missing" 2 \
  -p /tmp/input/nonexistent.txt -f json -o /tmp/data/output/output13.json

runTest "negative" "unsupported parameter is present" 2 \
  -p /tmp/input/nonexistent.txt -f json -o /tmp/data/output/output14.json --custom=argument

verifyAllTestsPassed
