package main

import "fmt"

func Greet(name string) string {
    return fmt.Sprintf("Hello, %s", name)
}

type Counter struct {
    count int
}

func (c *Counter) Increment() {
    c.count++
}