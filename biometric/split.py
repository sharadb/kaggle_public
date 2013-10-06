import io
import sys

def main():
  predictions_file = open(sys.argv[1])
  features_file = open(sys.argv[2])
  output_file = open(sys.argv[3], 'w')

  predicted_labels = predictions_file.readlines()

  for label in predicted_labels:
    label = int(label.replace('\n', ''))
    features = features_file.readline().replace('\n', '')
    gold_label = int(features.split(' ')[0])
    if gold_label != label:
      print >> output_file, features

if __name__ == '__main__':
  main()
