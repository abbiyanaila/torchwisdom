from torchwisdom.metrics.metrics import *
from torchwisdom.callback import Callback
import torchwisdom.metrics.functional as M
from torchwisdom.statemgr.state import StateManager
from torchwisdom.core import *


__all__ = ['AverageMetricsCallback', 'LossCallback', 'AccuracyCallback', 'AccuracyTopKCallback',
           'AccuracyThresholdCallback', 'ErrorRateCallback', 'MAECallback', 'MSECallback', 'RMSECallback',
           'MSLECallback', 'DiceCoefCallback']


class AverageMetricsCallback(Callback):
    def __init__(self, name='avg'):
        super(AverageMetricsCallback, self).__init__()
        self.metric_train = AverageMetrics()
        self.metric_valid = AverageMetrics()
        self.statemgr: StateManager = None
        self.name = name

    def on_fit_begin(self, *args: Any, **kwargs: Any) -> None:
        metric_state= self.statemgr.state.get('metric')
        train: Dict = metric_state.get('train')
        train[self.name] = {'val': [], 'mean': [], 'std': [], 'epoch': []}
        valid: Dict = metric_state.get('valid')
        valid[self.name] = {'val': [], 'mean': [], 'std': [], 'epoch': []}

    def on_epoch_begin(self, *args: Any, **kwargs: Any):
        self.metric_train.restart()
        self.metric_valid.restart()

    def on_epoch_end(self, *args: Any, **kwargs: Any) -> None:
        self.update_epoch_state('train')
        self.update_epoch_state('valid')

    def update_epoch_state(self, mode):
        metric_state: Dict = self.statemgr.state.get('metric')
        state = metric_state.get(mode).get(self.name)
        mean = state.get('mean')[-1]
        state.get('epoch').append(mean)

    def get_metric(self, mode) -> AverageMetrics:
        if mode == "train": return self.metric_train
        else: return self.metric_valid

    def get_state(self, mode) -> Dict:
        metric_state: Dict = self.statemgr.state.get('metric')
        return metric_state.get(mode).get(self.name)

    def update_state(self, mode):
        metric = self.get_metric(mode)
        state = self.get_state(mode)
        state.get('val').append(metric.value)
        state.get('mean').append(metric.mean)
        state.get('std').append(metric.std)

    def train_update(self): self.update_state('train')

    def valid_update(self): self.update_state('valid')


class LossCallback(AverageMetricsCallback):
    def __init__(self):
        super(LossCallback, self).__init__()
        self.name = 'loss'

    def on_train_forward_end(self, *args: Any, **kwargs: Any) -> None:
        loss = kwargs.get('loss')
        self.metric_train.update(loss.item())
        self.train_update()

    def on_validate_forward_end(self, *args: Any, **kwargs: Any) -> None:
        loss = kwargs.get('loss')
        self.metric_valid.update(loss.item())
        self.valid_update()


class AccuracyCallback(AverageMetricsCallback):
    def __init__(self):
        super(AccuracyCallback, self).__init__()
        self.name = 'acc'

    def on_train_forward_end(self, *args: Any, **kwargs: Any) -> None:
        # print('AccuracyCallback: on_forward')
        y_pred: Tensor = kwargs.get('y_pred')
        y_true: Tensor = kwargs.get('y_true')
        self.metric_train.update(M.accuracy(y_pred, y_true).item())
        self.train_update()

    def on_validate_forward_end(self, *args: Any, **kwargs: Any) -> None:
        y_pred: Tensor = kwargs.get('y_pred')
        y_true: Tensor = kwargs.get('y_true')
        self.metric_valid.update(M.accuracy(y_pred, y_true).item())
        self.valid_update()


class AccuracyTopKCallback(AverageMetricsCallback):
    def __init__(self, topk: tuple = (1,3)):
        super(AccuracyTopKCallback, self).__init__()
        self.topk = topk
        self.name = f'acc_topk{max(topk)}'

    def on_train_forward_end(self, *args: Any, **kwargs: Any) -> None:
        y_pred: Tensor = kwargs.get('y_pred')
        y_true: Tensor = kwargs.get('y_true')
        self.metric_train.update(M.accuracy_topk(y_pred, y_true, self.topk))
        self.train_update()

    def on_validate_forward_end(self, *args: Any, **kwargs: Any) -> None:
        y_pred = kwargs.get('y_pred')
        y_true = kwargs.get('y_true')
        self.metric_valid.update(M.accuracy_topk(y_pred, y_true, self.topk))
        self.valid_update()


class AccuracyThresholdCallback(AverageMetricsCallback):
    def __init__(self, threshold=0.5, sigmoid=False):
        super(AccuracyThresholdCallback, self).__init__()
        self.threshold = threshold
        self.sigmoid = sigmoid
        self.name = 'acc_thresh'

    def on_train_forward_end(self, *args: Any, **kwargs: Any) -> None:
        y_pred: Tensor = kwargs.get('y_pred')
        y_true: Tensor = kwargs.get('y_true')
        self.metric_train.update(M.accuracy_threshold(y_pred, y_true, self.threshold, self.sigmoid).item())
        self.train_update()

    def on_validate_forward_end(self, *args: Any, **kwargs: Any) -> None:
        y_pred: Tensor = kwargs.get('y_pred')
        y_true: Tensor = kwargs.get('y_true')
        self.metric_train.update(M.accuracy_threshold(y_pred, y_true, self.threshold, self.sigmoid).item())
        self.valid_update()


class ErrorRateCallback(AverageMetricsCallback):
    def __init__(self):
        super(ErrorRateCallback, self).__init__()
        self.name = 'error_rate'

    def on_train_forward_end(self, *args: Any, **kwargs: Any) -> None:
        y_pred: Tensor = kwargs.get('y_pred')
        y_true: Tensor = kwargs.get('y_true')
        self.metric_train.update(M.error_rate(y_pred, y_true).item())
        self.train_update()

    def on_validate_forward_end(self, *args: Any, **kwargs: Any) -> None:
        y_pred: Tensor = kwargs.get('y_pred')
        y_true: Tensor = kwargs.get('y_true')
        self.metric_valid.update(M.error_rate(y_pred, y_true).item())
        self.valid_update()


class MAECallback(AverageMetricsCallback):
    def __init__(self):
        super(MAECallback, self).__init__()
        self.name = 'mae'

    def on_train_forward_end(self, *args: Any, **kwargs: Any) -> None:
        y_pred: Tensor = kwargs.get('y_pred')
        y_true: Tensor = kwargs.get('y_true')
        self.metric_train.update(M.mean_absolute_error(y_pred, y_true).item())
        self.train_update()

    def on_validate_forward_end(self, *args: Any, **kwargs: Any) -> None:
        y_pred: Tensor = kwargs.get('y_pred')
        y_true: Tensor = kwargs.get('y_true')
        self.metric_valid.update(M.mean_absolute_error(y_pred, y_true).item())
        self.valid_update()


class MSECallback(AverageMetricsCallback):
    def __init__(self):
        super(MSECallback, self).__init__()
        self.name = 'mse'

    def on_train_forward_end(self, *args: Any, **kwargs: Any) -> None:
        y_pred: Tensor = kwargs.get('y_pred')
        y_true: Tensor = kwargs.get('y_true')
        self.metric_train.update(M.mean_squared_error(y_pred, y_true).item())
        self.train_update()

    def on_validate_forward_end(self, *args: Any, **kwargs: Any) -> None:
        y_pred: Tensor = kwargs.get('y_pred')
        y_true: Tensor = kwargs.get('y_true')
        self.metric_valid.update(M.mean_squared_error(y_pred, y_true).item())
        self.valid_update()


class RMSECallback(AverageMetricsCallback):
    def __init__(self):
        super(RMSECallback, self).__init__()
        self.name = 'rmse'

    def on_train_forward_end(self, *args: Any, **kwargs: Any) -> None:
        y_pred: Tensor = kwargs.get('y_pred')
        y_true: Tensor = kwargs.get('y_true')
        self.metric_train.update(M.root_mean_squared_error(y_pred, y_true).item())
        self.train_update()

    def on_validate_forward_end(self, *args: Any, **kwargs: Any) -> None:
        y_pred: Tensor = kwargs.get('y_pred')
        y_true: Tensor = kwargs.get('y_true')
        self.metric_valid.update(M.root_mean_squared_error(y_pred, y_true).item())
        self.valid_update()


class MSLECallback(AverageMetricsCallback):
    def __init__(self):
        super(MSLECallback, self).__init__()
        self.name = 'rmle'

    def on_train_forward_end(self, *args: Any, **kwargs: Any) -> None:
        y_pred: Tensor = kwargs.get('y_pred')
        y_true: Tensor = kwargs.get('y_true')
        self.metric_train.update(M.mean_squared_logarithmic_error(y_pred, y_true).item())
        self.train_update()

    def on_validate_forward_end(self, *args: Any, **kwargs: Any) -> None:
        y_pred: Tensor = kwargs.get('y_pred')
        y_true: Tensor = kwargs.get('y_true')
        self.metric_valid.update(M.mean_squared_logarithmic_error(y_pred, y_true).item())
        self.valid_update()


class DiceCoefCallback(AverageMetricsCallback):
    def __init__(self):
        super(DiceCoefCallback, self).__init__()
        self.name = 'dice_loss'

    def on_train_forward_end(self, *args: Any, **kwargs: Any) -> None:
        y_pred: Tensor = kwargs.get('y_pred')
        y_true: Tensor = kwargs.get('y_true')
        self.metric_train.update(M.dice_coeff(y_pred, y_true).item())
        self.train_update()

    def on_validate_forward_end(self, *args: Any, **kwargs: Any) -> None:
        y_pred: Tensor = kwargs.get('y_pred')
        y_true: Tensor = kwargs.get('y_true')
        self.metric_valid.update(M.dice_coeff(y_pred, y_true).item())
        self.valid_update()


if __name__ == '__main__':
    LossCallback()

