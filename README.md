# 🍷 Simulador de Ventas · Gira M19

Aplicación web construida con **Streamlit** para simular ganancias de ventas en la Gira M19. Permite estimar cuántas unidades se van a vender por producto y calcular en tiempo real el ingreso, costo y ganancia neta — tanto en pesos argentinos como en dólares.

---

## 📸 Funcionalidades

- **Lista de productos** agrupada por categoría (Vinos, Cerveza, Aceite de oliva, Alfajores, Aceitunas) con costo, precio de venta y margen unitario
- **Cotización USD** configurable para ver los resultados también en dólares
- **Carga de cantidades** estimadas por producto
- **Resumen automático**: Venta total, Costo total, Ganancia neta y Margen %
- **Detalle por producto** con tabla de resultados
- **Gráfico de barras** de ganancia por producto

---

## 🚀 Cómo correr la app

### 1. Clonar el repositorio

```bash
git clone https://github.com/marianoduran/Simulador_Productos_GiraM19.git
cd Simulador_Productos_GiraM19
```

### 2. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 3. Ejecutar la aplicación

```bash
streamlit run simulador_gira.py
```

La app se abre automáticamente en el navegador en `http://localhost:8501`.

---

## 📦 Dependencias

| Paquete | Versión mínima |
|---------|---------------|
| streamlit | 1.35.0 |
| pandas | 2.0.0 |

---

## 🗂 Estructura del proyecto

```
12_Simulador_Productos_GiraM19/
├── simulador_gira.py   # App principal de Streamlit
├── requirements.txt    # Dependencias Python
└── README.md           # Este archivo
```

---

## 📊 Fuente de datos

Los productos y precios provienen de la planilla **"Excel de productos Ventas junio 2026 M19"**, pestaña *Productos seleccionados*.

---

*Gira M19 · Junio 2026*
