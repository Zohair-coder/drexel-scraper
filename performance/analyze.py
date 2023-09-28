import pstats

p = pstats.Stats('performance/profile_output.pstat')
p.sort_stats('cumulative').print_stats(20)  # Top 10 time-consuming functions
