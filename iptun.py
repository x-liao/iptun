#!/usr/bin/env python3
import sys
import getopt
import os
import sqlite3
import subprocess
from prettytable import PrettyTable

PATH = os.path.split(os.path.realpath(__file__))[0]
db_name = PATH + "/tun.db"


class Sql(object):
	"""docstring for Sql"""

	def __init__(self, db_name):
		super(Sql, self).__init__()
		self.db_name = db_name

	def add(self, config):  # 添加隧道
		print(config)
		sql = """
		INSERT INTO tun(name,
		type,
		inte,
		remote,
		tun_ip,
		tun_gw,
		vlan,
		mtu,
		port,
		note)VALUES('%s','%s','%s','%s','%s','%s','%s',%d,%d,'%s');""" % (
			config["name"], config["type"], config["inte"],
			config["remote"], config["tun_ip"], config["tun_gw"], config["vlan"],
			config["mtu"], config["port"], config["note"])

		try:
			conn = sqlite3.connect(db_name)
			c = conn.cursor()
			c.execute(sql)
			conn.commit()
			conn.close()
			print("添加到数据库完成")
		except Exception as e:
			print("添加到数据库失败", e)

	def create(self):  # 创建数据库
		try:
			conn = sqlite3.connect(self.db_name)
			c = conn.cursor()
			c.execute('''CREATE TABLE tun(
				id integer PRIMARY KEY AUTOINCREMENT,
				name TEXT NOT NULL,
				type TEXT NOT NULL,
				inte TEXT NOT NULL,
				remote TEXT NOT NULL,
				tun_ip TEXT NOT NULL,
				tun_gw TEXT NOT NULL,
				vlan TEXT NOT NULL,
				mtu INT NOT NULL,
				port INT,
				note TEXT,
				UNIQUE (name),
				UNIQUE (tun_ip)
				);''')
			conn.commit()
			conn.close()
			print("创建数据库完成")
		except Exception as e:
			print("创建数据库失败", e)

	def select(self):  # 查询路由，在列出隧道时用到
		conn = sqlite3.connect(db_name)
		c = conn.cursor()
		c.execute("SELECT * FROM tun;")
		data = c.fetchall()
		conn.close()
		return data

	def select_id(self, field, id):  # 查询路由，在删除隧道时用到
		conn = sqlite3.connect(self.db_name)
		sql = "SELECT %s FROM tun where id=%d;" % (field, id)
		c = conn.cursor()
		c.execute(sql)
		data = c.fetchall()
		conn.close()
		return data

	def delete(self, id):
		try:
			conn = sqlite3.connect(self.db_name)
			sql = "DELETE from tun where id=%s;" % (id)
			print(sql)
			c = conn.cursor()
			c.execute(sql)
			conn.commit()
			conn.close()
			print("删除完成")
		except Exception as e:
			print("删除失败")


def show_table():  # 列出隧道表格
	table = PrettyTable(["id", "name", "type", "inte",
						 "remote", "tun_ip", "tun_gw", "vlan", "mtu",
											 "port", "note"])
	sq = Sql(db_name)
	data = sq.select()
	for x in data:
		list(x)
		table.add_row(x)
	return table


class Shell(object):
	"""docstring for shell"""

	def __init__(self):
		super(Shell, self).__init__()
		self.config = {}

	def print_help(self):
		print(
			'''
options:
	-a --add [name]             添加
	-d --del [id]               删除
	-p --port [port]            端口
	-r --remote [ip]            远程主机

			'''
		)

	def get_config(self):
		shortopts = 'lha:d:t:i:r:c:u:p:v:n:'
		longopts = ['add=', 'del=', 'type=', 'inte=',
					'remote=', 'mtu=', 'vlan=', 'port=', 'note=', 'list', 'help']

		try:
			optlist, args = getopt.getopt(sys.argv[1:], shortopts, longopts)

			for o, v in optlist:
				if o in ('-a', '--add'):
					self.config['name'] = v
					self.config['opt'] = "add"

				if o in ("-d", '--del'):
					self.config['opt'] = 'del'
					self.config['id'] = v

				if o in ("-t", '--type'):
					self.config['type'] = v

				if o in ('-i', '--inte'):
					self.config['inte'] = v

				if o in ('-r', '--remote'):
					self.config['remote'] = v

				if o in ('-c'):
					self.config['tun_ip'] = v

				if o in ('-u', '--mtu'):
					self.config['mtu'] = int(v)

				if o in ('-v]', '--vlan'):
					self.config['vlan'] = v

				if o in ('-p', '--port'):
					self.config['port'] = int(v)

				if o in ('-n', '--note'):
					self.config['note'] = v

				if o in ('-l', '--list'):
					self.config['opt'] = "list"
				if o in ('-h', '--help'):
					self.config['help'] = "help"
					self.print_help()
					sys.exit(2)

		except getopt.GetoptError as e:
			print(e)
			self.print_help()
			sys.exit(2)

		if not self.config:
			self.print_help()
			self.config = self.loop()

		return self.config

	def loop(self):
		while True:
			cmd = input('>>>')
			if cmd == 'add':
				return self.add_config()
			elif cmd == 'del':
				return self.del_config()
			elif cmd == 'list' or cmd == 'ls':
				print(show_table())
			elif cmd == 'exit':
				exit(0)

	def add_config(self):
		self.config['opt'] = 'add'
		print('''
选择隧道类型：
	1. gre
	2. ipip
			''')
		
		type_num = input('隧道类型(1 2)：')
		if type_num == '2':
			self.config['type'] == 'ipip'
		else:
			self.config['type'] = 'gre'
		print('选择gre')
		self.config['name'] = input('隧道名称：')
		inte_dic = list_inte()
		inte_num = input('选择网卡：')
		if not inte_num:
			print('未选择网卡')
			exit()
		for k,v in inte_dic.items():
			if v == int(inte_num):
				self.config['inte'] = k
		print('选择的网卡ip:',get_ip(self.config['inte']))
		self.config['remote'] = input('远程ip：')
		self.config['tun_ip'] = input('本地隧道ip：')
		self.config['mtu'] = input('设置MTU：')
		if self.config['mtu']:
			try:
				self.config['mtu'] = int(self.config['mtu'])
			except Exception as e:
				print('mtu必须是数字')
				self.config.pop('mtu')
		else:
			self.config.pop('mtu')

		self.config['note'] = input('备注：')
		return self.config

	def del_config(self):
		self.config['opt'] = 'del'
		print(show_table())
		self.config['id'] = int(input('删除的ID：'))
		return self.config


def get_ip(inte):
	cmd = "ip addr | grep -E %s | grep inet | awk -F '/' '{print $1}' | awk '{print $2}'" % inte
	pipe = subprocess.Popen(
		cmd,
		shell=True,
		stderr=subprocess.PIPE,
		stdout=subprocess.PIPE)

	for x in pipe.communicate():
		if x:
			ret = x.decode("utf-8").replace('\n', '')
			return ret
	return False

def list_inte():
	inte_list = [i for i in os.listdir('/sys/class/net') if 'ppp' not in i]
	i=0
	inte_dic = {}
	for inte in inte_list:
		inte_dic[inte] = i
		ip = get_ip(inte)
		print("%d: %s\t\t\t%s"%(i,inte,ip))
		i += 1
	return inte_dic


class Tun(object):
	"""docstring for Tun"""

	def __init__(self):
		super(Tun, self).__init__()

	def create(self, config):
		config['local_ip'] = get_ip(config['inte'])
		os.system('ip tunnel %s %s mode %s remote %s local %s' % (config['opt'],
					config['name'], config['type'], config['remote'], config['local_ip']))

		os.system('ip link set %s up mtu %d' % (config['name'], config['mtu']))
		os.system('ip addr add %s/24 dev %s' %
				  (config['tun_ip'], config['name']))

	def delete(self, name):
		print('ip tunnel del %s' %name)
		os.system('ip tunnel del %s' %name)


def check_key(config):
	par = ('name', 'type', 'inte', 'remote', 'tun_ip', 'tun_gw')  # 必须参数
	par1 = ('tun_gw', 'vlan', 'mtu', 'port', 'note')  # 可选参数，如果空，为默认值
	for x in par1:
		if x not in config.keys():
			if x == 'tun_gw':
				config['tun_gw'] = ''
			if x == 'vlan':
				config['vlan'] = ''
			if x == 'mtu':
				config['mtu'] = 1450
			if x == 'port':
				config['port'] = 0
			if x == 'note':
				config['note'] = ''

	for x in par:
		if x not in config.keys():
			if x == 'tun_gw':
				config['tun_gw'] = ''
			print('缺少参数', x)
			exit()
	return config


def main():
	db = Sql(db_name)
	tun = Tun()
	if not os.path.exists(db_name):
		db.create()

	shell = Shell()
	config = shell.get_config()

	if config['opt'] == "add":
		config = check_key(config)
		db.add(config)
		tun.create(config)

	elif config['opt'] == "list":
		print(show_table())

	elif config['opt'] == "del":
		try:
			name = db.select_id('name', config['id'])[0][0]
			tun.delete(name)
			db.delete(config['id'])
		except Exception as e:
			print('ID不存在')

if __name__ == '__main__':
	main()
