# Remote manager client
# by Leonty Kopytov @leontyko

from fastapi import FastAPI, HTTPException
import uvicorn
import json
import os.path
import asyncio
import subprocess
import pyautogui
from sys import platform
import webbrowser

options = {
	"listen_port": 8000, # прослушиваемый порт
	"log_level": "info", # уровень логирования uvicorn: critical, error, warning, info, debug, trace
	"browser_path": "C:/Program Files (x86)/Google/Chrome/Application/chrome.exe %s", # путь до браузера, если хотим открывать не дефолтный
    "applications": { # список приложений на устройстве
		# Пример: (указываем в формате: название - команда для запуска)
        "notepad": "notepad.exe",
    },
	"links": { # список подготовленных ссылок (линков) на устройстве
		"youtube": "youtube.com", # указываем в формате: название - ссылка
	}
}

pwr_task = None
	
app = FastAPI()
		
async def doPowerTask(cmd, delay):
	global pwr_task
	try:
		await asyncio.sleep(delay*60) # так как задержка в секундах - умножаем на 60
		if platform == "win32": # Windows
			if cmd == "shutdown":
				subprocess.Popen(["shutdown", "/s", "/t", "0"])
			elif cmd == "reboot":
				subprocess.Popen(["shutdown", "/r"])
			elif cmd == "sleep":
				subprocess.Popen(["shutdown", "/h"])
		elif platform == "linux" or platform == "linux2": # Linux
			if cmd == "shutdown":
				subprocess.Popen(["shutdown", "-h", "now"])
			elif cmd == "reboot":
				subprocess.Popen(["reboot"])
			elif cmd == "sleep":
				subprocess.Popen(["pm-suspend"])
		elif platform == "darwin": # Mac
			if cmd == "shutdown":
				subprocess.Popen(["shutdown", "-h", "now"])
			elif cmd == "reboot":
				subprocess.Popen(["shutdown", "-r", "now"])
			elif cmd == "sleep":
				subprocess.Popen(["shutdown", "-s", "now"])
	except asyncio.CancelledError:
		pwr_task = None
	finally:
		pwr_task = None

@app.get("/")
async def home():
	json_data = json.dumps({"result": "ok"})
	return json_data
		
@app.get("/applications")
async def app_list():
	applist = []
	for app in options['applications']:
		applist.append(app)
	json_data = json.dumps({"result": "ok", "applications": applist})
	return json_data

@app.get("/links")
async def url_list():
	linklist = []
	for link in options['links']:
		linklist.append(link)
	json_data = json.dumps({"result": "ok", "links": linklist})
	return json_data
	
@app.get("/power")
async def pwrManagement(cmd:str, delay:int=0):
	global pwr_task
	power_cmds = ["shutdown", "reboot", "sleep"]
	if cmd in power_cmds:
		if pwr_task is None:
			result = "ok"
			detail = "Задача успешно создана"
		else:
			pwr_task.cancel()
			result = "ok"
			detail = "Задача создана заново"
		pwr_task = asyncio.create_task(doPowerTask(cmd, delay), name=cmd)
	else:
		result = "Error"
		detail = "Команда не найдена"
	json_data = json.dumps({"result": result, "detail": detail})
	return json_data
	
@app.get("/volume")
async def volManagement(cmd:str, point:int=1):
	vol_cmds = ["up", "down", "mute", "max"]
	if cmd in vol_cmds:
		if cmd == "up":
			for i in range(point):
				pyautogui.press("volumeup")
		elif cmd == "down":
			for i in range(point):
				pyautogui.press("volumedown")
		elif cmd == "mute":
			pyautogui.press("volumemute")
		elif cmd == "max":
			for i in range(50):
				pyautogui.press("volumeup")
		result = "ok"
		detail = ""
	else:
		result = "Error"
		detail = "Команда не найдена"
	json_data = json.dumps({"result": result, "detail": detail})
	return json_data
	
@app.get("/cancel")
async def cancelPowerTask():
	global pwr_task
	if pwr_task is not None:
		pwr_task.cancel()
		result = "ok"
		detail = "Задача успешно отменена"
	else:
		result = "Error"
		detail = "Нет запущенных задач"
	json_data = json.dumps({"result": result, "detail": detail})
	return json_data
    
@app.get("/application")
async def startApp(cmd:str, delay:int=0):
	apps = options['applications']
	result = "Error"
	detail = "Приложение не найдено"
	for app in apps:
		if app == cmd:
			try:
				subprocess.Popen(cmd)
				result = "ok"
				detail = "Приложение выполнено"
			except:
				detail = "Ошибка запуска приложения"
	json_data = json.dumps({"result": result, "detail": detail})
	return json_data

@app.get("/browser")
async def openLink(cmd:str):
	if cmd in options['links']:
		cmd = options['links'][cmd]
	browser_path = options["browser_path"]
	try:
		webbrowser.get(browser_path).open(cmd)
		result = "ok"
		detail = "Ссылка открыта в браузере"
	except:
		try:
			webbrowser.open(cmd) #If not get browser then open default
			result = "ok"
			detail = "Ссылка открыта в стандартном браузере"
		except:
			result = "Error"
			detail = "Ошибка открытия браузера"
	json_data = json.dumps({"result": result, "detail": detail})
	return json_data

@app.get("/media")
async def media(cmd:str):
	media_cmds = ["playpause", "nexttrack", "prevtrack"]
	if cmd in media_cmds:
		pyautogui.press(cmd)
		result = "ok"
		detail = "Команда выполнена"
	else:
		result = "Error"
		detail = "Команда не найдена"
	json_data = json.dumps({"result": result, "detail": detail})
	return json_data

if __name__ == "__main__":
	uvicorn.run("reman_client:app", host="0.0.0.0", port=options["listen_port"],log_level=options["log_level"])