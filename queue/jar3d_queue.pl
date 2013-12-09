#!/usr/bin/perl

use strict;
use warnings;

use threads;
use threads::shared;
use Thread::Queue;
use DBI;
use FindBin qw($RealBin);

### Global Variables ###

# Maximum working threads
my $MAX_THREADS = 4;

# Flag to inform all threads that application is terminating
my $TERM :shared = 0;

# Threads add their ID to this queue when they are ready for work
# Also, when app terminates a -1 is added to this queue
my $IDLE_QUEUE = Thread::Queue->new();

# CPU time out for each query in seconds
my $TIMEOUT = 1800;

# refresh time
my $SLEEP = 5;

### Database Connection ###
# $RealBin contains the location of the script
my %config = do $RealBin . '/jar3d_queue_config.pl';
my $dsn = 'DBI:mysql:' . $config{db_database}. ':localhost';
my $dbh = DBI->connect($dsn, $config{db_user_name}, $config{db_password});

### Signal Handling ###

# Gracefully terminate application on ^C or command line 'kill'
$SIG{'INT'} = $SIG{'TERM'} =
    sub {
        print(">>> Terminating <<<\n");
        $TERM = 1;
        # Add -1 to head of idle queue to signal termination
        $IDLE_QUEUE->insert(0, -1);
    };


### Main Processing Section ###
MAIN:
{
    ### INITIALIZE ###

    # Thread work queues referenced by thread ID
    my %work_queues;

    # Create the thread pool
    for (1..$MAX_THREADS) {
        # Create a work queue for a thread
        my $work_q = Thread::Queue->new();

        # Create the thread, and give it the work queue
        my $thr = threads->create('worker', $work_q);

        # Remember the thread's work queue
        $work_queues{$thr->tid()} = $work_q;
    }


    ### DO WORK ###

    # Manage the thread pool until signalled to terminate
    while (! $TERM) {

       # get the queries
       my @queries = get_queries();

       if ( scalar(@queries) > 0 ) {
            # Wait for an available thread
            my $tid = $IDLE_QUEUE->dequeue();

            # Check for termination condition
            last if ($tid < 0);

            # Give the thread some work to do
            my $query_id = pop(@queries);

            my $work = "ulimit -t $TIMEOUT; java  -jar $RealBin/webJAR3D_server.jar /Users/API/Models/IL/1.8/lib/all.txt $query_id $config{db_user_name} $config{db_password} $config{db_database}";
            $work_queues{$tid}->enqueue($work);
        }
        sleep($SLEEP);
    }


    ### CLEANING UP ###

    # Signal all threads that there is no more work
#    $work_queues{$_}->enqueue(-1) foreach keys(%work_queues);
    $work_queues{$_}->enqueue('') foreach keys(%work_queues);

    # Wait for all the threads to finish
    $_->join() foreach threads->list();

    $dbh->disconnect;
}

print("Done\n");
exit(0);


### Thread Entry Point Subroutines ###

# A worker thread
sub worker
{
    my ($work_q) = @_;

    # This thread's ID
    my $tid = threads->tid();

    # Work loop
     while (! $TERM) {
        # Indicate that were are ready to do work
        printf("Idle     -> %2d\n", $tid);
        $IDLE_QUEUE->enqueue($tid);

        # Wait for work from the queue
        my $work = $work_q->dequeue();

        # If no more work, exit
        last if ($work eq '');

        # Do some work while monitoring $TERM
        printf("            %2d <- Working\n", $tid);
        while (! $TERM) {
            system($work);
            last;
        }

        # Loop back to idle state if not told to terminate
    }

    # All done
    printf("Finished -> %2d\n", $tid);
}

sub get_queries
{
    my $statement = "select query_id from jar3d_query_info where status = 0;";

    my $sth = $dbh->prepare($statement);
    $sth->execute();

    my @query_ids = ();

    while (my $result = $sth->fetchrow_hashref()) {
        print "Value returned: $result->{query_id}\n";
        push @query_ids, $result->{query_id};
    }

    $sth->finish;

    return @query_ids;
}

__END__