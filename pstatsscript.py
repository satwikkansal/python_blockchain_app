import pstats

p = pstats.Stats("statstest")
p.sort_stats("time").print_stats(100)
