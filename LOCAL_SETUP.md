# Instructions for setting up a local environment to run labs in place of GitHub Codespace


<br><br>

These instructions will guide you through configuring a local environment that you can use to do the labs. 

<br><br>


**1. Use Git to clone this repository down to your machine with a command like the following.**

```
git clone https://github.com/skilldevai/ae-day3-b
```

<br><br>

**2. Open up the cloned project in VS Code.** 

There are multiple ways to do this: 
- You can drag and drop the project directory onto VS Code.
- You can open VS Code and open the folder from its menu.
- You can simply change into the cloned directory and run the command "code ."

```
cd ae-day3-b
code .
```

<br><br>

**3. Once you open the folder/project in VS Code, VS Code should detect the devcontainer setup and prompt you about running it as a development container (usually in lower right corner). Do not choose this option. Instead just click on the "x" to close the dialog and ignore that option.** 

<br>

![Starting in VS Code](./images/local-5-b.png?raw=true "Starting in VS Code")

<br>


**4. Run the commands below to setup the python env and startup Ollama.**

```
scripts/pysetup.sh py_env && scripts/startup_ollama.sh
```

**5. Allow the setup processing to run automatically. (May take up to 10 minutes for some projects).**

<br>

![Setup](./images/local-6-b.png?raw=true "Setup")

<br><br>


**6. You are now ready to run the labs in your local environment!**

**NOTE: For any paths in the labs that reference `/workspaces/ae-day3-b` you should use the directory of your clone instead.

<br><br>

---

## License and Use

These materials are provided as part of the **Enterprise AI Accelerator Workshop** conducted by **TechUpSkills (Brent Laster)**.

Use of this repository is permitted **only for registered workshop participants** for their own personal learning and
practice. Redistribution, republication, or reuse of any part of these materials for teaching, commercial, or derivative
purposes is not allowed without written permission.

© 2026 TechUpSkills / Brent Laster. All rights reserved.
