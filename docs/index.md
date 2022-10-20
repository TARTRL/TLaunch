{!README.md!}

## Introduction

[Deepmind launchpad](https://github.com/deepmind/launchpad) is a library that
helps writing distributed program in a simple way. But currently it only
supports (or has only open-sourced) launching programs on a single host, either
multi-threaded or multi-processed. This library provides a way of launching existing launchpad programs on multiple
nodes. Only some simple modification to your program is needed.