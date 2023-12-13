#!/bin/bash

# Check if gRPC tools are installed
if python3 -c "import grpc_tools.protoc" &> /dev/null; then
    echo "gRPC tools are installed"
else
    echo "gRPC tools are not installed"
fi

# Check if alembic is installed
if python3 -c "import alembic" &> /dev/null; then
    echo "Alembic is installed"
else
    echo "Alembic is not installed"
fi

SRC_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
cd $SRC_DIR

# gRPC files generation
python3 -m grpc_tools.protoc -I../protos --python_out=. --pyi_out=. --grpc_python_out=. ../protos/auth.proto
python3 -m grpc_tools.protoc -I../protos --python_out=. --pyi_out=. --grpc_python_out=. ../protos/conversation.proto
python3 -m grpc_tools.protoc -I../protos --python_out=. --pyi_out=. --grpc_python_out=. ../protos/event.proto

# Database migration
alembic -c alembic.ini upgrade head
