from bilmo.scripts.config import Config
from bilmo.scripts.initialize import initialize
from bilmo.dataset.prepare_datasets_dataframe import load_data_train, load_data_test
from bilmo.dataset.create_databunch import create_databunch, get_cached_data, print_data_cls_info, print_data_test_info
from bilmo.learner.create_learner import create_learner
from bilmo.learner.test_cafa import test_cafa
from bilmo.callbacks.tensorboard import add_tensorboard
import logging

log = logging.getLogger("cafa-logger")
conf = Config.conf

if __name__ == "__main__":
    initialize()
    data_cls, data_test = get_cached_data()
    df_test = load_data_test() # needed for cafa3_testing at the end
    if data_cls is None:
        df_train, df_valid = load_data_train()
        data_cls, data_test = create_databunch(df_train, df_valid, df_test)
    learn_cls = create_learner(data_cls)

    if conf['add_tensorboard']:
        add_tensorboard(learn_cls)

    if not conf['skip_training']:
        lr = 2e-2
        log.info('freeze')
        learn_cls.freeze()
        learn_cls.fit_one_cycle(1, lr, moms=(0.8, 0.7))

        if not conf['just_one_epoch']:
            learn_cls.fit_one_cycle(4, lr, moms=(0.8, 0.7))
            #
            learn_cls.save('cls-v1-0-' + conf['datetime'])

            log.info('unfreeze')
            learn_cls.freeze_to(-2)
            learn_cls.fit_one_cycle(2, slice(lr/(2.6**4), lr), moms=(0.8, 0.7))
            # learn_cls.save('cls-v1-1-' + conf['datetime'])

            learn_cls.freeze_to(-3)
            learn_cls.fit_one_cycle(2, slice(lr/2/(2.6**4), lr/2), moms=(0.8, 0.7))
            # learn_cls.save('cls-v1-2-' + conf['datetime'])

            learn_cls.unfreeze()
            learn_cls.fit_one_cycle(4, slice(lr/10/(2.6**4), lr/10), moms=(0.8, 0.7))
            # learn_cls.save('cls-v1-3-' + conf['datetime'])

            learn_cls.fit_one_cycle(20, slice(lr/10/(2.6**4), lr/10), moms=(0.8, 0.7))
            learn_cls.save('cls-v1-4-' + conf['datetime'])
            # learn_cls.export(file = 'export/' + 'export-cls-v1-4-' + datetime_str+ '.pkl')
        else:
            log.info('just_one_epoch is True')

        log.info('Done Training')
    else:
        log.info('Skipped training')
    # print('full valid validation: loss, acc, f_beta', learn_cls.validate(learn_cls.data.test_dl))

    if conf['test_on_cafa3_testset']:
        log.info('Start Test Prediction')
        test_cafa(data_test, learn_cls, df_test)
    log.info('The End - run-classifier.py')
