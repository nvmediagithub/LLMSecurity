# Фича Analysis

## Обзор

Фича **Analysis** предоставляет унифицированную систему для комплексного анализа результатов тестирования и атак на слои защиты LLM. Она объединяет метрики производительности, выявляет уязвимости и генерирует детализированные отчеты для оценки эффективности системы безопасности.

## Архитектура

```text
src/llm_security/features/analysis/
├── domain/
│   ├── entities.py          # AnalysisResult, UnifiedReport, LayerMetrics
│   └── interfaces.py        # IAnalysisService
├── application/
│   ├── analysis_service.py  # AnalysisService - унифицированный сервис анализа
│   ├── result_analyzer.py   # ResultAnalyzer - анализатор результатов
│   ├── metrics_calculator.py # расчет метрик
│   └── report_generator.py  # генератор отчетов
└── infrastructure/
    ├── report_exporters.py  # экспортеры отчетов (CSV, JSON, HTML)
    └── result_repository.py # хранение результатов анализа
```

## Принципы унифицированной архитектуры

### 1. Комплексный анализ

Фича объединяет результаты тестирования [`TestRunResult`](src/llm_security/features/testing/domain/results.py) и результатов атак [`AttackResult`](src/llm_security/features/attacks/domain/entities.py) в единый анализ [`AnalysisResult`](src/llm_security/features/analysis/domain/entities.py).

### 2. Метрики по слоям защиты

Анализ предоставляет детальные метрики для каждого слоя защиты:

```python
@dataclass(slots=True)
class LayerMetrics:
    layer_id: str
    blocks_count: int = 0
    rewrites_count: int = 0
    escalates_count: int = 0
    allows_count: int = 0
    false_positives: int = 0
    average_latency_ms: float = 0.0
    effectiveness_score: float = 0.0

    @property
    def total_decisions(self) -> int:
        return self.blocks_count + self.rewrites_count + self.escalates_count + self.allows_count

    @property
    def block_rate(self) -> float:
        return (self.blocks_count / self.total_decisions * 100) if self.total_decisions else 0.0
```

### 3. Метрики по категориям атак

Анализ паттернов атак по категориям:

```python
@dataclass(slots=True)
class AttackMetrics:
    category: str
    total_attempts: int = 0
    successful_attempts: int = 0
    blocked_attempts: int = 0

    @property
    def success_rate(self) -> float:
        return (self.successful_attempts / self.total_attempts * 100) if self.total_attempts else 0.0

    @property
    def block_rate(self) -> float:
        return (self.blocked_attempts / self.total_attempts * 100) if self.total_attempts else 0.0
```

### 4. Унифицированные отчеты

Единый формат отчетов [`UnifiedReport`](src/llm_security/features/analysis/domain/entities.py) с поддержкой множественных форматов экспорта.

## API Reference

### AnalysisService

Основной сервис для анализа:

```python
class AnalysisService(IAnalysisService):
    def analyze_results(
        self,
        test_results: List[TestRunResult],
        attack_results: List[AttackResult]
    ) -> AnalysisResult:
        """Анализировать комбинированные результаты тестов и атак."""

    def generate_report(self, analysis_result: AnalysisResult) -> UnifiedReport:
        """Генерировать унифицированный отчет из результатов анализа."""
```

### ResultAnalyzer

Анализатор результатов с выявлением уязвимостей:

```python
class ResultAnalyzer:
    def analyze_results(
        self,
        test_results: List[TestRunResult],
        attack_results: List[AttackResult]
    ) -> AnalysisResult:
        """Анализировать результаты и выявлять уязвимости."""

    def _identify_vulnerabilities(...) -> List[str]:
        """Идентифицировать уязвимости в системе безопасности."""

    def _generate_recommendations(...) -> List[str]:
        """Генерировать рекомендации по улучшению безопасности."""
```

### MetricsCalculator

Расчет метрик производительности:

```python
class MetricsCalculator:
    def calculate_layer_metrics(
        self,
        test_results: List[TestRunResult],
        attack_results: List[AttackResult]
    ) -> List[LayerMetrics]:
        """Рассчитать метрики для каждого слоя защиты."""

    def calculate_attack_metrics(self, attack_results: List[AttackResult]) -> List[AttackMetrics]:
        """Рассчитать метрики по категориям атак."""

    def calculate_overall_metrics(...) -> Dict[str, int]:
        """Рассчитать общие метрики системы."""
```

### ReportGenerator

Генератор унифицированных отчетов:

```python
class ReportGenerator:
    def generate_report(self, analysis_result: AnalysisResult) -> UnifiedReport:
        """Генерировать отчет с executive summary и рекомендациями."""
```

### Экспортеры отчетов

Интерфейс и реализации для экспорта отчетов:

```python
class IReportExporter(ABC):
    @abstractmethod
    def export(self, report: UnifiedReport, output_path: str) -> None:
        """Экспортировать отчет в указанный путь."""

    @property
    @abstractmethod
    def file_extension(self) -> str:
        """Расширение файла для данного экспортера."""

class CSVReportExporter(IReportExporter): ...
class JSONReportExporter(IReportExporter): ...
class HTMLReportExporter(IReportExporter): ...
```

## Примеры использования

### Базовый анализ результатов

```python
from llm_security.features.analysis.application.analysis_service import AnalysisService

# Создание сервиса анализа
analysis_service = AnalysisService()

# Анализ результатов тестов и атак
analysis_result = analysis_service.analyze_results(test_results, attack_results)

print(f"Test Pass Rate: {analysis_result.test_pass_rate:.1f}%")
print(f"Attack Block Rate: {analysis_result.attack_block_rate:.1f}%")
```

### Работа с метриками слоев

```python
# Получение метрик по слоям
for layer_metric in analysis_result.layer_metrics:
    print(f"Layer {layer_metric.layer_id}:")
    print(f"  Effectiveness: {layer_metric.effectiveness_score:.1f}%")
    print(f"  False Positives: {layer_metric.false_positives}")
    print(f"  Block Rate: {layer_metric.block_rate:.1f}%")
    print(f"  Avg Latency: {layer_metric.average_latency_ms:.2f}ms")
```

### Анализ паттернов атак

```python
# Анализ успешности атак по категориям
for attack_metric in analysis_result.attack_metrics:
    print(f"Category {attack_metric.category}:")
    print(f"  Success Rate: {attack_metric.success_rate:.1f}%")
    print(f"  Total Attempts: {attack_metric.total_attempts}")
    print(f"  Blocked: {attack_metric.blocked_attempts}")
```

### Выявление уязвимостей

```python
# Получение списка идентифицированных уязвимостей
vulnerabilities = analysis_result.vulnerabilities
for vuln in vulnerabilities:
    print(f"Vulnerability: {vuln}")

# Получение рекомендаций
recommendations = analysis_result.recommendations
for rec in recommendations:
    print(f"Recommendation: {rec}")
```

### Генерация и экспорт отчетов

```python
from llm_security.features.analysis.infrastructure.report_exporters import (
    CSVReportExporter, JSONReportExporter, HTMLReportExporter
)

# Генерация унифицированного отчета
report = analysis_service.generate_report(analysis_result)

# Экспорт в различные форматы
csv_exporter = CSVReportExporter()
csv_exporter.export(report, "analysis_report.csv")

json_exporter = JSONReportExporter()
json_exporter.export(report, "analysis_report.json")

html_exporter = HTMLReportExporter()
html_exporter.export(report, "analysis_report.html")
```

## Интеграция с существующими фичами

### Testing

Фича Analysis интегрируется с [`TestRunResult`](src/llm_security/features/testing/domain/results.py) для анализа результатов тестирования prompt injection сценариев.

### Attacks

Использует [`AttackResult`](src/llm_security/features/attacks/domain/entities.py) для анализа результатов симуляции атак на слои защиты.

### Reporting

Расширяет возможности [`MetricsAggregator`](src/llm_security/features/reporting/application/aggregator.py), предоставляя более детальный анализ с выявлением уязвимостей и рекомендациями.

### Defense Pipeline

Анализирует метрики производительности [`DefensePipeline`](src/llm_security/features/defense/application/pipeline.py), включая latency и эффективность блокировок.

### Layers

Работает с [`LayerManager`](src/llm_security/features/layers/application/layer_manager.py) для получения информации о конфигурации и статусе слоев.

### UI

PyQt интерфейс может использовать результаты анализа для отображения dashboard с метриками, графиками уязвимостей и интерактивными рекомендациями.

## Миграционные гайды

### Обновление существующих анализаторов

1. **Интеграция с AnalysisService**: Обновите существующие анализаторы для использования унифицированного интерфейса:

```python
# Вместо прямого анализа
# metrics = aggregator.calculate_metrics(test_results)

# Используйте AnalysisService
analysis_service = AnalysisService()
analysis_result = analysis_service.analyze_results(test_results, attack_results)
metrics = analysis_result.layer_metrics
```

### Обновление форматов отчетов

Обновите существующие экспортеры для использования [`UnifiedReport`](src/llm_security/features/analysis/domain/entities.py):

```python
# Вместо старого формата
# class OldReportExporter:
#     def export(self, metrics: dict, path: str):

# Используйте новый интерфейс
class NewReportExporter(IReportExporter):
    def export(self, report: UnifiedReport, output_path: str):
        # Экспорт унифицированного отчета
```

### Интеграция с новыми метриками

Добавьте расчет новых метрик в [`MetricsCalculator`](src/llm_security/features/analysis/application/metrics_calculator.py):

```python
def calculate_custom_metrics(self, test_results, attack_results):
    """Рассчитать дополнительные метрики."""
    # Логика расчета кастомных метрик
    return custom_metrics
```

### Обновление UI компонентов

Обновите UI для отображения новых метрик:

```python
# В PyQt контроллере
def update_analysis_display(self, analysis_result):
    # Отображение новых метрик
    self.test_pass_rate_label.setText(f"{analysis_result.test_pass_rate:.1f}%")
    self.attack_block_rate_label.setText(f"{analysis_result.attack_block_rate:.1f}%")

    # Отображение уязвимостей
    for vuln in analysis_result.vulnerabilities:
        self.add_vulnerability_item(vuln)
```

## Заключение

Фича Analysis предоставляет мощную систему для комплексного анализа безопасности LLM, объединяя:

- **Унифицированный анализ** результатов тестов и атак
- **Детальные метрики** по слоям и категориям атак
- **Автоматическое выявление уязвимостей** с рекомендациями
- **Множественные форматы экспорта** отчетов
- **Интеграцию со всеми фичами** системы

Эта архитектура значительно улучшает возможности мониторинга и анализа безопасности, позволяя оперативно выявлять проблемы и принимать обоснованные решения по улучшению защиты.