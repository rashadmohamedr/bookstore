from environs import Env

env = Env()
env.read_env()

bind = "0.0.0.0:8000"
CPU_CORES = 8
workers = env("workers",default=2 * CPU_CORES + 1) # max
accesslog = "-"