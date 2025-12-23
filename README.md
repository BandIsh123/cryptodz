## Команды

Все запускаемся через main.py / main_zksync.py

## 2 задание

### Для минта L2Pass

```bash
l2pass --qty 1 --value 1
```

Параметры:

* `qty` — количество NFT (по умолчанию 1)
* `value` — значение в POL

---

### Для свапа QuickSwap

```bash
swap --from ETH --to USDC --amount 0.000001 --slippage 0.5
```

Параметры:

* `from` — токен, из которого меняем
* `to` — токен, в который меняем
* `amount` — сумма
* `slippage` — допустимый slippage (%)

---

## 3 задание (часть 1, zkSync / SpaceFi)

### 1. ETH → USDT

```bash
eth_to_usdt --amount 0.000001 --slippage 0.5
```

### 2. ETH → WBTC

```bash
eth_to_wbtc --amount 0.000001 --slippage 0.5
```

### 3. USDC.e → ETH

```bash
usdc_e_to_eth --amount 0.001 --slippage 0.5
```

Использовать весь баланс:

```bash
usdc_e_to_eth --all --slippage 0.5
```

### 4. USDT → ETH

```bash
usdt_to_eth --amount 0.01 --slippage 0.5
```

### 5. USDT → USDC.e

```bash
usdt_to_usdc_e --amount 0.001 --slippage 0.5
```

### 6. WBTC → ETH

```bash
wbtc_to_eth --amount 0.0000001 --slippage 0.5
```

---

## 3 задание (часть 2, zkSync / Koi, SpaceFi, Maverick, SyncSwap)

### 1. KoiFinance

USDC.e → ETH:

```bash
koi_usdc_e_to_eth --amount 1 --slippage 0.5
```

ETH → USDC.e:

```bash
koi_eth_to_usdc_e --amount 0.000001 --slippage 0.5
```

---

### 2. SpaceFi

ETH → USDT:

```bash
eth_to_usdt --amount 0.000001 --slippage 0.5
```

USDC.e → ETH:

```bash
usdc_e_to_eth --amount 0.01 --slippage 0.5
```

Использовать весь баланс:

```bash
usdc_e_to_eth --all
```

---

### 3. Maverick

USDC.e → ETH:

```bash
mav_usdc_e_to_eth --amount 0.01 --slippage 0.5
```

USDC.e → MAV:

```bash
mav_usdc_e_to_mav --amount 0.01 --slippage 0.5
```

---

### 4. SyncSwap

USDC.e → ETH:

```bash
sync_usdc_e_to_eth --amount 0.01 --slippage 0.5
```
