
INSERT INTO accounts (name, description) VALUES
	 ('Zurich','Main investment account in Zurich'),
	 ('Fideuram','Fideuram Direct account');

INSERT INTO instruments (isin, ticker,name,category,currency) VALUES
	 ('LU0290356871','X13E.MI','DB X-T.II IB.SETR1-3','acc','EUR'),
	 ('LU0290355717','XGLE','DB X-T.II IBX ETF 1C','acc','EUR'),
	 ('IE00B579F325','SGLD.MIX','INVESCO PHYSIC GOLD','acc','EUR'),
	 ('IE00B53QG562','CSEMU','ISHAR CORE MSCI ETF','acc','EUR'),
	 ('IE00B4L5Y983','SWDA','ISHARES CORE MSCI WO','acc','EUR'),
	 ('IE00B0M62X26','IBCI','ISHARES EU INFL LINK','acc','EUR'),
	 ('IE00B53SZB19','CSNDX','ISHARES NASDAQ100','acc','EUR'),
	 ('IE00B3FH7618','IEGE','ISHS EUR GO 0-1  EUR','acc','EUR'),
	 ('IE00B3VWN179','CSBGU3','ISHARES USD GV 1-3 B','acc','EUR'),
	 ('IE00B1FZS798','IBTM','ISHARES USD TRSB7-10','dist','EUR');
INSERT INTO instruments (isin, ticker,name,category,currency) VALUES
	 ('IE000OJ5TQP4','NATO','HANetf Future of Defence UCITS ETF','acc','EUR'),
	 ('US70450Y1038','','PAYPAL HOLDINGS INC ','acc','EUR');

INSERT INTO trades (instrument_id,account_id, date,"type",quantity,price,description) VALUES
	 (1,1,'2025-10-12 19:23:51.458937','buy',191,16385,NULL),
	 (2,1,'2025-10-12 19:23:51.458937','buy',151,20897,NULL),
	 (3,1,'2025-10-12 19:23:51.458937','buy',139,19018,NULL),
	 (4,1,'2025-10-12 19:23:51.458937','buy',150,19586,NULL),
	 (5,1,'2025-10-12 19:23:51.458937','buy',324,8652,NULL),
	 (6,1,'2025-10-12 19:23:51.458937','buy',142,22153,NULL),
	 (7,1,'2025-10-12 19:23:51.458937','buy',30,107389,NULL),
	 (8,1,'2025-10-12 19:23:51.458937','buy',301,9893,NULL),
	 (9,1,'2025-10-12 19:23:51.458937','buy',302,10843,NULL),
	 (10,1,'2025-10-12 19:23:51.458937','buy',205,16015,NULL);
INSERT INTO trades (instrument_id,account_id,date,"type",quantity,price,description) VALUES
	 (7,1,'2025-10-13 17:14:40.111039','sell',30,121991,NULL);


INSERT INTO transactions (account_id, trade_id, date, "type",amount,description) VALUES
	 (1, 11,'2025-10-13 17:14:40.112017','fee',3900,'Fees for SELL of 30x ISHARES NASDAQ100'),
	 (1, 11,'2025-10-13 17:14:40.112537','tax',113896,'Capital gains tax on sale of 30x ISHARES NASDAQ100');
