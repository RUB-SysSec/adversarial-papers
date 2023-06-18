#!/bin/bash

build()
{
    docker build -t adversarial-papers .
}

shell() 
{
    if [ ! -f "docker.sh" ]; then
        echo "Please invoke the script from the base dir of the project."
        exit
    fi
    docker run -v $PWD/evaluation/models:/root/adversarial-papers/evaluation/models \
               -v $PWD/evaluation/corpus:/root/adversarial-papers/evaluation/corpus \
               -v $PWD/evaluation/trials:/root/adversarial-papers/evaluation/trials \
               -v $PWD/evaluation/targets:/root/adversarial-papers/evaluation/targets \
               -v $PWD/evaluation/submissions:/root/adversarial-papers/evaluation/submissions \
               -v $PWD/evaluation/scripts:/root/adversarial-papers/evaluation/scripts \
               -v $PWD/evaluation/plots:/root/adversarial-papers/evaluation/plots \
               -v $PWD/evaluation/problemspace/llms:/root/adversarial-papers/evaluation/problemspace/llms \
               -v $PWD/evaluation/problemspace/synonyms:/root/adversarial-papers/evaluation/problemspace/synonyms \
               --rm -it adversarial-papers bash
}

run(){
    if [ ! -f "docker.sh" ]; then
        echo "Please invoke the script from the base dir of the project."
        exit
    fi
    docker run -v $PWD/evaluation/models:/root/adversarial-papers/evaluation/models \
               -v $PWD/evaluation/corpus:/root/adversarial-papers/evaluation/corpus \
               -v $PWD/evaluation/trials:/root/adversarial-papers/evaluation/trials \
               -v $PWD/evaluation/targets:/root/adversarial-papers/evaluation/targets \
               -v $PWD/evaluation/submissions:/root/adversarial-papers/evaluation/submissions \
               -v $PWD/evaluation/scripts:/root/adversarial-papers/evaluation/scripts \
               -v $PWD/evaluation/plots:/root/adversarial-papers/evaluation/plots \
               -v $PWD/evaluation/problemspace/llms:/root/adversarial-papers/evaluation/problemspace/llms \
               -v $PWD/evaluation/problemspace/synonyms:/root/adversarial-papers/evaluation/problemspace/synonyms \
               --rm -it adversarial-papers $1
}

print_usage() 
{
    echo "Choose: docker.sh {build|shell}"
    echo "    build - Build the container"
    echo "    shell - Spawn a shell inside the container"
    echo "    run   - Run a command inside the container"
}

if [[ $1 == "" ]]; then
    echo "No argument provided"
    print_usage
elif [[ $1 == "build" ]]; then
    build
elif [[ $1 == "shell" ]]; then
    shell 
elif [[ $1 == "run" ]]; then
    run "$2"
else 
    echo "Argument not recognized!"
    print_usage
fi