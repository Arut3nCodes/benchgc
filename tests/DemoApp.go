package main

import (
	"fmt"
	"math/rand"
	"runtime"
	"time"
)

type Payload struct {
	Data []byte
}

func main() {
	fmt.Println("Starting Go GC demo workload...")

	rand.Seed(time.Now().UnixNano())

	var store []Payload

	ticker := time.NewTicker(50 * time.Millisecond)
	statsTicker := time.NewTicker(2 * time.Second)

	for {
		select {
		case <-ticker.C:
			// Allocate random blocks (10KB – 200KB)
			size := rand.Intn(200*1024-10*1024) + 10*1024
			buf := make([]byte, size)

			// Touch memory
			for i := 0; i < len(buf); i += 4096 {
				buf[i] = byte(rand.Intn(256))
			}

			store = append(store, Payload{Data: buf})

			// Drop old references to force GC
			if len(store) > 200 {
				store = store[len(store)/2:]
			}

		case <-statsTicker.C:
			var m runtime.MemStats
			runtime.ReadMemStats(&m)

			fmt.Printf(
				"heap_alloc=%dKB heap_sys=%dKB num_gc=%d\n",
				m.HeapAlloc/1024,
				m.HeapSys/1024,
				m.NumGC,
			)
		}
	}
}
