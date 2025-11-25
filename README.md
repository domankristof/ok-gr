# "OK GR"
Your personal AI-powered coach that draws on your race data to offer tailored insight, custom teaching points and summaries/logs of data to help you reach the podium. 

## 1. High Level Overview
### 1.1 The Problem
* Most amateur GR-Cup teams don’t have a dedicated race engineer analysing their data or giving structured coaching. After researching typical team workflows, I realised how big this gap really is.

* OK-GR was born from the idea of giving every driver their own AI race engineer, a tool that makes drivers and teams more competitive.

### 1.2 The Solution - OK-GR
* My goal with OK-GR is to ex the data layer and make the data easily digestible for non-specialised drivers, allowing them to gain valuable insight into how to improve their pace, through their data.
* The concept is to make raw CSV data as palatable as possible for amature teams, making the series more accessible, more competite and overall easier to enter into.
* Idea is to have a highly personalisable dashboard, with the GR-Agent focusing entirely on where you are struggling the most.

### 1.3 How this Helps the Drivers of the GR-Cup
* Gives smaller teams without specialised engineers an ability to utilise their data.
* Coaches the driver to improve their driving, making the teams more competitive.
* Makes the series more enticing for skilled drivers without large teams and deep technical skills.

## 2. How it Works
### 2.1 Static Data Summaries
Currently, the following graphical summaries of your uploaded data are available when you enter a coaching session:
1. **Speed-Distance Plots** - two traces are combined in one plot to compare the average of your mid race push laps with your fastest overall lap. This allows you to see where you are loosing time (slower) compared to your fastest lap.

2. **Race Session Timing Metrics** - key metrics displayed are; personal best lap time, final position, fastest lap in the race and difference to the fastest lap in the race.

3. **Weather Condition Metrics** - averaged key metrics displayed are; air temperature, track temperature, wind speed, humidity and rain events (Boolean).

4. **G-G Plot & Traction Margins** - plot of lateral versus longitudinal acceleration to analyse the traction usage of the driver. An approximated traction ellipse is calculated and displayed, allong with two reference-G circles, to allow the driver to see how much more grip they have available which they are not using (if there is a significant margin to the traction ellipse, the driver can push harder as they have not reached the traction boundary of their tyres).

4. **Sector Timing Metrics** - key metrics displayed are; breakdown of personal best sector times, differences of personal sector times to fastest driver, optimal lap comparison to the fastest lap of the session.

### 2.2 Interactive AI Race Engineer
On the right hand side of the page, you have access to a chat window to your personal AI race engineer. Here you can ask GR-Agent to assist you with the following:

## 3. Current Functional Capabilties of Your Race Engineer
Due to the limited time I had to prototype, GR-Agent currently has only a couple tools at its disposal to analyse and coach you on your race data. Your race engineer can assist you with:

1. **Analysis of Vehicle Telemetry Files**
    * Analysis of steering smoothness via a smoothness score, micro corrections, steering ussage overview.

2. **Analysis of Sector Times, Deltas and Lap Times**
    * Feedback/coaching on lap and sectors times, and comparisons to the race leader. 
    * Computation of optimal lap and its deltas, where this would place the driver.
    * Suggestions on which sectors driver can improve the most and coaching on how they can improve their driving.

3. **Creation of a Downloadable Coaching Summart Document**


## 4. How to Use OK-GR
1. Download the files from this link: click here

2. Open the app and naviagte to the file upload centre.

3. Enter your vehicle number and select the telemetry session which corresponds to the track and race session data that you have just downloaded.

4. Upload the respective files under each upload section (i.e. "Top 10 Laps File", "Weather File"...).

5. Click on submit - you will now be redirected to a data analysis session.

6. View your data summary and chat with your personal AI race engineer.

7. When you have finished your session, ask GR-Agent to prepare you a downloadable coaching summary.


## 5. Important Notes
1.  Please use dark theme/ dark-mode on your device/browser to improve the UI apperance.

2. If you are trying OK-GR, please select a telemetry session from the dropdown that has acceleration and GPS data. Some telemetry datasets are deficient of these parameters and may throw an error.

## 6. What Next For OK-GR
1. Integrate voice-to-speech coaching to allow hands-free interaction.

2. Share the tool with GR-Cup drivers for real-world testing and see how we can itterate on OK-GR.

3. I would like to also explore integrating OK-GR into consumer GR cars as a track-day training assistant. The car would pull together telemetry data during your session outing, and between sessions you can debrief with GR-Agent and they will coach you on how you can improve, based on your fresh data. Conversing through natural language.
