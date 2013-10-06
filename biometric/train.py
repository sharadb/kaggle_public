import argparse
import io
import os
import sys

parser = argparse.ArgumentParser()
parser.add_argument('--train_file', help='The train.csv file downloaded from kaggle',
                    default='data/train.csv')
parser.add_argument('--generate_features_script', help='The script file that generates the features',
                    default='train_model.py')
parser.add_argument('--should_generate_features', help='If true, calls the generate_features_script else uses features_file',
                    action='store_true')
parser.add_argument('--split_script', help='Script that splits correct and incorrect classifications',
                    default='split.py')
parser.add_argument('--model_prefix', help='Prefix for the output model files', default='data/logR.boosted_model')
parser.add_argument('--features_prefix', help='Prefix for the output features files', default='data/logR.boosted_features')
parser.add_argument('--num_models', help='Number of models that should be output', type=int, default=1)
parser.add_argument('--train_binary', help='Path to the train binary of LIBLINEAR', default='~/biometric/liblinear-1.93/train')
parser.add_argument('--predict_binary', help='Path to the predict binary of LIBLINEAR', default='~/biometric/liblinear-1.93/predict')
args = parser.parse_args()

def ExecuteCommand(cmd):
  print >>sys.stderr, 'Executing %s' % (cmd)
  os.system(cmd)

def GetLineCount(filename):
  print >>sys.stderr, 'Running wc -l %s' % (filename)
  result = os.popen('wc -l %s' % (filename)).read()
  return int(result.split()[0])

def main():
  print args
  if args.should_generate_features:
    ExecuteCommand('python %s %s %s' % (args.generate_features_script,
                                        args.train_file,
                                        args.features_prefix + '1'))

  weights = []

  for i in range(1, args.num_models + 1):
    features_file = args.features_prefix + str(i)
    model_file = args.model_prefix + str(i)
    if i != 1:
      ExecuteCommand('%s -s 0 %s %s' % (args.train_binary,
                                        features_file,
                                        model_file))
    if i != args.num_models:
      predicted_labels_file = '/tmp/predicted_labels'
      ExecuteCommand('%s -b 0 %s %s %s' % (args.predict_binary,
                                           features_file,
                                           model_file,
                                           predicted_labels_file))
      ExecuteCommand('python %s %s %s %s' % (args.split_script,
                                             predicted_labels_file,
                                             features_file,
                                             args.features_prefix + str(i + 1)))

  for i in range(1, args.num_models + 1):
    line_count = GetLineCount(args.features_prefix + str(i))
    weights.append(line_count + 0.)
  total = sum(weights)
  normalized_weights = [x / total for x in weights]

  ExecuteCommand('python predict.py --num_models %d --weights %s' % (
      args.num_models,
      ' '.join(map(str, normalized_weights))))

if __name__ == '__main__':
  main()
