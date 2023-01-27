

results = ["A","B","C","D","E","F"]

newResults = ["A","X","D","E","F","B","C"]#["D","E","F","A","B","C"]

def find(a, b):
    for i, e in enumerate(a):
        if e == b:
            return i
    return -1

i = 0
while newResults and i < len(results):
    if results[i] == newResults[0]:
        newResults.pop(0)
        i += 1
        continue
    srcIdx = find(results[i:], newResults[0])
    print("SRC", srcIdx)
    if srcIdx == -1:
        results = results[:i]
        break
    elif srcIdx > 0:
        results = results[:i] + results[i+srcIdx:]

    print(results, newResults)
    
    dstIdx = find(newResults, results[i])
    print("DST", dstIdx)
    if dstIdx > 0:
        results = results[:i] + newResults[:dstIdx] + results[i:]
        newResults = newResults[dstIdx:]
        i += dstIdx

results += newResults

print(results)