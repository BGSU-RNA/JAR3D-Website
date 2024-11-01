"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

import os
import sys

sys.path.append('/var/www/jar3d')  # add your project directory to the path
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'

import django
django.setup()

from django.test import TestCase
from django.db import transaction

from app import views
from app.models import Query_sequences


class SimpleTest(TestCase):
    def test_basic_addition(self):
        """
        Tests that 1 + 1 always equals 2.
        """
        self.assertEqual(1 + 1, 2)

class FungalSeqTest(TestCase):
    def setUp(self):
        self.ss = '..((((...((((((.......((...........((((..((((.....(((((.....(((((...((((((.......)))))).......((((((((((((((....((((((...))))))))((((..(((.(((.(((((((.....((.((((((.......(((((....))))).)))))).)).)).......))))))))....)))..)))).))))).)))).)))(((((.(((...((((((((((((((.........................(((((((((((.((..(((......))))))))))))))))(((((((((...((((((.....))))))...))))))).))((((((......))))))))))))))).............)))))...)))))))).......................)))))........)))))....))))..)))).))......))))))))))....((((....((((..........................((.(((..(((.(((..........)))......)))..))).))....))))....))))......................'
        self.seq = ['GUGAGU---GACCUCU-UCUUUCCU-CUACUCGUUUCGCACCCCACCA-CCCAAUUUUCUGGGGGCUCUCUCCAA-CCUUAUGGAGAACCCCAAACCCGCACUGCGUCUGUU-CUCGACAAUCGA-GACGUUCUUCCACCCGUGACGAGG------UCCGCGCGCG-UUUUCGAUCGCUUGAUCGCCGCGUGGA--CCGCUGCAUACGUCCGGUC-AUGGUUGGACGCGCGGUUGUGUGGUGAAAUGGGGGGCUGAGCGAGGAGUGCGGAAAAGAC-AGCAGUAUAUCCCUCUGGGAGCUG-------------------------------CAUGGUUGGAUAACCGACUGCACUCGCUGUGACGCAGUUUGAGUGGCAUGUC---GGCGAUGCACUUUUUA------CUCGAUUCACGUAGCCCCCUGUGUAACCGUUUUCAGCGUUGUACCCGUUGAU---------------UGGGACACAGACAACGCGCCACCUUCCAUGUUCGAGCG------------------------------CACGCUGACAUUUUGGUCUCUAUAUCCUU--------------CUCAUCCCUCGAAUUGGAUCGUUG--------CAUAAUGUAAG']
        validator = views.JAR3DValidator()
        fasta = []
        (self.loops, self.indices) = validator.isfolded_extract_loops(self.ss,self.seq)
        # use query_id, query_type, and parsed_input equal to '1' for testing, seems like a bad idea
        self.query_info = validator.make_query_info('1','1','1')
        self.query_seqs = validator.make_query_sequences(self.loops, fasta, '1')
        self.query_inds = validator.make_query_indices(self.indices,'1')

        # old
        # [seq.save() for seq in self.query_seqs]

        with transaction.atomic():
            for seq in self.query_seqs:
                print(f"Attempting to save: {seq}")
                try:
                    seq.save()
                except Exception as e:
                    print(f"Error saving sequence {seq}: {e}")
                    raise  # Optionally, re-raise the error to stop execution

        # for seq in self.query_seqs:
        #     try:
        #         seq.save()
        #     except Exception as e:
        #         print(f"Error saving sequence {seq}: {e}")

        self.query_seqs_db = Query_sequences.objects.filter(query_id='1')
    def test_fungal_ss_reader(self):
        self.assertEqual(len(self.loops.keys()),35)
    def test_fungal_dict_convert(self):
        self.assertEqual(len(self.query_seqs),35)
    def test_fungal_db_saver(self):
        self.assertEqual(len(self.query_seqs_db),35)

class ViroidSeqTest(TestCase):
    def setUp(self):
        self.ss =   '.((((((((.((.((((((((.(.((((.((((((..(((((.((((((...(((........(((((((((((.((...((((((((..((((((((.....(((((((((.(.((((...((((..(((((((.(((.((..((((.((.((((((.....((((..((((.(((((....)))))...))))..)))).....))))).))).)))).))..))).))))))).))))))).).))))))))))......))))).)))..)..))))))))))))))..)))))).........)))...)).)))).)))).).))))))..)))))..)))))))))))))))))).'
        self.seq = ['CGGAACUAAACUCGUGGUUCCUGUGGUUCACACCUGACCUCCUGAGCAGAAAAGA-AAAAAGAAGGCGGCUCGGAGGAGCGCUUCAGGGAUCCCCGGGGAAACCUGGAGCGAACUGGCA-AUAAGGACGGUGGGGAGUGCCC-AGCGGCCGACAGGAGUAAUUCCCGCCGAAACAGGGUUUUCACCCUUCCUUUCUUCGGGUGUCCUUCCUCGCGCCCGCAGGACCACCCCUCGCCCCCUUUGCGCUGUCGCUUCGGAUAUUACCCGGUGGAAACAACUGAAGCUCCCGAGAACCGCUUUUUCUC-UAUCUUUCUUUGCUUCGGGGCGAGGGUGUUUAGCCCUUGGAACCGCAGUUGGUUCCU']
        validator = views.JAR3DValidator()
        fasta = []
        (self.loops, self.indices) = validator.isfolded_extract_loops(self.ss,self.seq)
        self.query_info = validator.make_query_info('1','1','1')
        self.query_seqs = validator.make_query_sequences(self.loops, fasta, '1')
        self.query_inds = validator.make_query_indices(self.indices,'1')


                # try:
                #     setattr(seq, field.name, value)
                #     seq.save(update_fields=[field.name])
                # except TypeError as e:
                #     print(f"Field {field.name} is causing the issue")
                #     raise e

        with transaction.atomic():
            for seq in self.query_seqs:
                print("Attempting to save this entry:")
                for field in seq._meta.fields:
                    value = getattr(seq, field.name)
                    print(f"Field: {field.name}, Value: {value}, Type: {type(value)}")

                try:
                    seq.save()
                except Exception as e:
                    print(f"Error saving sequence {seq}: {e}")
                    raise  # Optionally, re-raise the error to stop execution


        # [seq.save() for seq in self.query_seqs]


        self.query_seqs_db = Query_sequences.objects.filter(query_id='1')
    def test_fungal_ss_reader(self):
        self.assertEqual(len(self.loops.keys()),34)
    def test_fungal_dict_convert(self):
        self.assertEqual(len(self.query_seqs),33)
    def test_fungal_db_saver(self):
        self.assertEqual(len(self.query_seqs_db),33)

class AlignmentMakerTest(TestCase):
    def setUp(self):
        self.single_loop = 'CAG*CGG\n'
        self.fasta_loop = '>Loop1\nCAG*CGG\n'
        self.ss = '((...))\nCCAAAGG\n'
        self.fasta_ss = '((...))\n>Sequence1\nCCAAAGG\n'
        self.parsed_single_loop = views.make_input_alignment(self.single_loop,'isNoFastaSingleLoop')
        self.parsed_fasta_loop = views.make_input_alignment(self.fasta_loop,'isFastaSingleLoop')
        self.parsed_ss = views.make_input_alignment(self.ss,'isNoFastaSingleLoop')
        self.parsed_fasta_ss = views.make_input_alignment(self.fasta_ss,'isFastaSingleLoop')
    def test_single_loop(self):
        self.assertEqual(self.single_loop,self.parsed_single_loop)
    def test_fasta_loop(self):
        self.assertEqual(self.fasta_loop,self.parsed_fasta_loop)
    def test_ss(self):
        self.assertEqual(self.parsed_ss,'  1    2    3    4    5    6    7  \n  C    C    A    A    A    G    G  \n')
    def test_fasta_ss(self):
        self.assertEqual(self.parsed_fasta_ss,'  1    2    3    4    5    6    7  \n>Sequence1\n  C    C    A    A    A    G    G  \n')