#!/bin/bash
# Hourly subnet watcher. Logs to watch.log; appends findings to notification.md.
cd /root/Bittensor/Subnet-Analyze || exit 1
{
  echo "=== $(date -u '+%Y-%m-%d %H:%M UTC') ==="
  nice -n 19 /usr/bin/python3 watch.py 2>&1
} >> watch.log
# keep the log from growing without bound
tail -n 2000 watch.log > watch.log.tmp && mv watch.log.tmp watch.log
