import re
import subprocess
from tcping import Ping
from logger import get_logger
import time
import functools

PING_TIME = 10
LOGGER  = get_logger()

def ping_retry(num_retries, wait_time):
    def decorator(ping_func):
        @functools.wraps(ping_func)
        def wrapper(ip_addr, *args, **kwargs):
            for i in range(num_retries):
                if ping_func(ip_addr, *args, **kwargs):
                    return True
                else:
                    LOGGER.warning(f"IP {ip_addr} 异常，等待{wait_time}秒后{i}/{num_retries}次重试")
                    time.sleep(wait_time)
            LOGGER.warning(f"IP {ip_addr} 无法连接")
            return False
        return wrapper
    return decorator

@ping_retry(num_retries=3, wait_time=5)
def ping_ip(ip_addr, ping_time=PING_TIME):
    LOGGER.info(f"检查IP{ip_addr}")
    try:
        # 执行系统的 ping 命令
        output = subprocess.check_output(['ping', '-c', f'{ping_time}', ip_addr])
        # 从输出结果中提取丢包率
        packet_loss = re.search(r'(\d+)% packet loss', output.decode('utf-8'))
        if packet_loss:
            loss_rate = packet_loss.group(1)
            # print(loss_rate, packet_loss)
            if loss_rate != 100:
                LOGGER.info(f"IP正常, 丢包率{loss_rate}%")
                return True

        LOGGER.warning(f"IP异常, 丢包率100%")
        return False

    except subprocess.CalledProcessError as e:
        LOGGER.error(f"Ping failed: {e}")
        return False
    except Exception as e:
        LOGGER.error(f"An error occurred: {e}")
        return False

@ping_retry(num_retries=3, wait_time=5)
def tcpping_ip(ip_addr, ping_time=PING_TIME):
    LOGGER.info(f"检查IP{ip_addr}")
    
    ping = Ping(ip_addr)
    ping.ping(ping_time)
    success_rate = ping.result.rows[0].success_rate

    if success_rate == "0.00%":
        LOGGER.warning(f"IP异常, {success_rate}")
        return False
    else:
        LOGGER.info(f"IP正常, {success_rate}")
        return True