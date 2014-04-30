"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.test import TestCase
from JAR3Dresults import views
from JAR3Dresults.models import Query_sequences

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

    def test_fungal_seq(self):
        validator = views.JAR3DValidator()
        fasta = []
        (loops, indices) = validator.isfolded_extract_loops(self.ss,self.seq)
        query_info = validator.make_query_info('1','1','1')
        query_seqs = validator.make_query_sequences(loops, fasta, '1')
        query_inds = validator.make_query_indices(indices,'1')
        [seq.save() for seq in query_seqs]
        query_seqs_db = Query_sequences.objects.filter(query_id='1')
        self.assertEqual(len(loops.keys()),35)
        self.assertEqual(len(query_seqs),35)
        self.assertEqual(len(query_seqs_db),35)