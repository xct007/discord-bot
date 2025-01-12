import os
import time
import shutil
import subprocess
import logging

# Constants
TEMP_FOLDER = f"temp_{int(time.time())}"
CLIENT_FOLDER = "client"
OPENAPI_SCHEMA = "https://scdn.lovita.io/openapi/itsrose.json"
GENERATOR_YAML = "generator.yaml"
LIBS_FOLDER = "libs"
REPO_PATH = os.getcwd()

# Configure logging
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] - %(message)s")


def create_libs_folder():
	logging.info(f"Creating libs folder: {LIBS_FOLDER}")
	os.makedirs(LIBS_FOLDER, exist_ok=True)


def create_temp_folder():
	logging.info(f"Creating temporary folder: {TEMP_FOLDER}")
	os.makedirs(TEMP_FOLDER, exist_ok=True)


def create_generator_yaml():
	logging.info(f"Creating generator YAML: {GENERATOR_YAML}")
	content = f"""
project_name_override: {TEMP_FOLDER}
package_name_override: {CLIENT_FOLDER}
"""
	with open(GENERATOR_YAML, "w") as file:
		file.write(content)


def clean_client_folder():
	if os.path.exists(CLIENT_FOLDER):
		logging.info(f"Removing existing client folder: {CLIENT_FOLDER}")
		shutil.rmtree(CLIENT_FOLDER)
	create_temp_folder()


def update_repo():
	logging.info("Updating repository")
	try:
		subprocess.run(
			["git", "pull"],
			check=True,
			cwd=REPO_PATH,
			stdout=subprocess.DEVNULL,
			stderr=subprocess.DEVNULL,
		)
		logging.info("Repository updated successfully.")
	except subprocess.CalledProcessError:
		logging.error("Failed to update repository.")


def install_package(package):
	logging.info(f"Installing package: {package}")
	try:
		subprocess.run(
			["pip", "install", package],
			check=True,
			stdout=subprocess.DEVNULL,
			stderr=subprocess.DEVNULL,
		)
		logging.info(f"Package {package} installed successfully.")
	except subprocess.CalledProcessError:
		logging.error(f"Failed to install {package}.")


def generate_openapi_client():
	logging.info("Generating OpenAPI client...")
	install_package("openapi-python-client")
	try:
		subprocess.run(
			[
				"openapi-python-client",
				"generate",
				"--url",
				OPENAPI_SCHEMA,
				"--config",
				GENERATOR_YAML,
				"--overwrite",
			],
			check=True,
			stdout=subprocess.DEVNULL,
			stderr=subprocess.DEVNULL,
		)
		shutil.copytree(
			os.path.join(TEMP_FOLDER, CLIENT_FOLDER), LIBS_FOLDER, dirs_exist_ok=True
		)
		logging.info(f"Copied files to {LIBS_FOLDER}")
	except subprocess.CalledProcessError:
		logging.error("Failed to generate OpenAPI client.")


def cleanup():
	logging.info("Cleaning up temporary files.")
	shutil.rmtree(TEMP_FOLDER, ignore_errors=True)
	os.remove(GENERATOR_YAML)
	
	logging.info("Uninstalling openapi-python-client")
	try:
		subprocess.run(
			["pip", "uninstall", "openapi-python-client", "-y"],
			check=True,
			stdout=subprocess.DEVNULL,
			stderr=subprocess.DEVNULL,
		)
		logging.info("openapi-python-client uninstalled successfully.")
	except subprocess.CalledProcessError:
		logging.error("Failed to uninstall openapi-python-client.")


def main():
	create_libs_folder()
	clean_client_folder()
	create_generator_yaml()
	update_repo()
	generate_openapi_client()
	cleanup()


if __name__ == "__main__":
	main()
