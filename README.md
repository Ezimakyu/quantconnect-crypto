# quantconnect-crypto
I was mainly playing around with algorithmic crypto trading. I created a model which takes in historical data on a crypto (mainly tested on Bitcoin USDT) and calculated "indicators" of these data, and then makes decisions on whether to buy/sell/do nothing every hour.   

Both files of code are only runnable on the QuantConnect environment (they have their own libraries and such): \
https://www.quantconnect.com/ 

main.py is for running model on historical data and testing its performance. \
research.ipynb is for investigating different indicators and seeing how good they could be for the model. 

Example run (one of the better results - most of mine ended up having losses lol): 

<img width="1822" height="654" alt="image" src="https://github.com/user-attachments/assets/d065780a-01ac-4cc3-8664-dd79a93ced9b" />
