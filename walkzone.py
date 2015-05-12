#!/usr/bin/python

import getopt
import string
import sys
import netaddr
import datetime

import dns.message
import dns.query
import dns.rdatatype
import dns.resolver
import dns.message
import dns.rdata
import dns.rdatatype
import dns.flags
from dns.dnssec import algorithm_to_text

from netaddr import *

from lib.dnshelper import DnsHelper
from lib.msf_print import *

# domain_list = set(open('co.domains', 'r').read().split())
# domain_list = set(open('demo_domains.txt', 'r').read().split())
# domain_list = set(domain_list[1:200])
# domain_list = set(['abilicaonline.se'])

def write_to_file(data, target_file):
    """
    Function for writing returned data to a file
    """
    with open(target_file, 'w') as fp:
        for i in data:
            fp.write('%s\n' % (i,))

def get_a_answer(target, ns, timeout):
    query = dns.message.make_query(target, dns.rdatatype.A, dns.rdataclass.IN)
    query.flags += dns.flags.CD
    query.use_edns(edns=True, payload=4096)
    query.want_dnssec(True)
    answer = dns.query.udp(query, ns, timeout)
    return answer

def get_next_local():
    global local_file 
    return local_file.pop()

def get_next(target, ns, timeout):
    next_host = None
    response = get_a_answer(target, ns, timeout)
    for a in response.authority:
        if a.rdtype == 47:
            for r in a:
                next_host = r.next.to_text()[:-1]
    return next_host

def get_ds_answer(target, ns, timeout):
    ADDITIONAL_RDCLASS = 65535
    domain = dns.name.from_text(target)
    if not domain.is_absolute():
        domain = domain.concatenate(dns.name.root)

    query = dns.message.make_query(domain, dns.rdatatype.DS)
    query.flags |= dns.flags.AD
    query.find_rrset(query.additional, dns.name.root, ADDITIONAL_RDCLASS,
                       dns.rdatatype.OPT, create=True, force_unique=True)
    answer = dns.query.udp(query, ns, timeout)
    return answer

def get_ds_answer_old(target, ns, timeout):
    query = dns.message.make_query(target, dns.rdatatype.DS, dns.rdataclass.IN)
    query.flags += dns.flags.CD
    query.use_edns(edns=True, payload=4096)
    query.find_rrset(query.additional, dns.name.root, 65535,
                   dns.rdatatype.OPT, create=True, force_unique=True)
    query.want_dnssec(True)
    answer = dns.query.udp(query, ns, timeout)
    return answer

def dns_sec_check_DS(domain, ns, timeout):
    """
    Check if a zone is configured for DNSSEC by asking the DS to the parent
    """
    try:
        answer = get_ds_answer(domain, ns, timeout)
        if answer.answer:
            return True
        return False
    except dns.resolver.NXDOMAIN:
        print_error("Could not resolve domain: {0}".format(domain))
        sys.exit(1)

    except dns.exception.Timeout:
        print_error("A timeout error occurred please make sure you can reach the target DNS Servers")
        print_error("directly and requests are not being filtered. Increase the timeout from {0} second".format(timeout))
        print_error("to a higher number with --lifetime <time> option.")
        # sys.exit(1)
    except dns.resolver.NoAnswer:
        print_error("DNSSEC is not configured for {0}".format(domain))

def ds_zone_walk(original_domain, ns, request_timeout):
    """
    Perform DNSSEC Zone Walk using NSEC records found the the error additional
    records section of the message to find the next host to query int he zone.
    """
    records = set()
    dnssec_domains = set()
    original_dom = original_domain
    parent = ""
    host = None
    counter = 0
    counterDNSSEC = 0
    
    pending = set([original_domain])
    finished = set()
    transformations = set()

    try:
        for server in ns:
            print "Using ns:", server
            try:
                while pending:
                    domain_name = pending.pop()
                    finished.add(domain_name)
                    # Get next hostname
                    # print "asking for:", domain_name
                    if run_local:
                        try:
                            regNSEC = get_next_local()
                        except Exception, e:
                            print 'regNSEC error:', e
                            break
                    else:                        
                        regNSEC = get_next(domain_name, server, request_timeout)
                                
                    if regNSEC is None:
                        parent = ""
                        temp = domain_name.split(".")
                        host = temp[0]
                        for k in temp:
                            if k != host:
                                parent += k + "."
                        parent = parent[:-1]
                        # print "host: ", host, " parent: ", parent

                        # Make transformations
                        transformations.add("{0}-.{1}".format(host, parent)) 
                        transformations.add("{0}0.{1}".format(host, parent)) 
                        transformations.add("{0}{1}.{2}".format(host, host[-1] , parent)) 
                        transformations.add("0.{0}".format(original_dom))
                        # print transformations

                        for t in transformations:
                            #print "trying:", t
                            response = get_a_answer(t, server, request_timeout)
                            for a in response.authority:
                                if a.rdtype == 47:
                                    for r in a:
                                        nsec_found = r.next.to_text()
                                        # print counter, " nsec_found: ", nsec_found, " query: ", t
                                        if nsec_found not in records and nsec_found != '0-0.se.':
                                            records.add(nsec_found)
                                            pending.add(nsec_found)
                                            counter += 1
                                            dnssecEnabled = dns_sec_check_DS(nsec_found, server, request_timeout)
                                            if dnssecEnabled is True:
                                                counterDNSSEC += 1
                                                print "%d/%d\t%s\tYES" % (counterDNSSEC, counter, nsec_found)
                                                dnssec_domains.add(nsec_found)
                                            else:
                                                print "%d/%d\t%s\tNO" % (counterDNSSEC, counter, nsec_found)
                        transformations = set()

                    else:
                        # Add hostname to list
                        #print counter, " domain: ", regNSEC, " query: ", domain
                        records.add(regNSEC)
                        pending.add(regNSEC)
                        counter += 1
                        dnssecEnabled = dns_sec_check_DS(regNSEC, server, request_timeout)
                        if dnssecEnabled:
                            counterDNSSEC += 1
                            print "%d/%d\t%s\tYES" % (counterDNSSEC, counter, regNSEC)
                            dnssec_domains.add(regNSEC)
                        else:
                            print "%d/%d\t%s\tNO" % (counterDNSSEC, counter, regNSEC)
                        # print counter, "/", counterDNSSEC, " ", regNSEC

                    # Ensure nothing pending has already been queried
                    pending -= finished
                         
            except (dns.exception.Timeout):
                print_error("A timeout error occurred while performing the zone walk please make ")
                print_error("sure you can reach the target DNS Servers directly and requests")
                print_error("are not being filtered. Increase the timeout to a higher number")
                print_error("with --lifetime <time> option.")

    except (KeyboardInterrupt):
        print_error("You have pressed Ctrl + C. Saving found records.")
    
    # Give a summary of the walk
    if len(records) > 0:
        print_good("{0} records found".format(len(records)))
        print_good('DNSSEC domains: {0}'.format(len(dnssec_domains)))
    else:
        print_error("Zone could not be walked")
    
    # Save the records
    if autosave:
        with open('domains_retrieved_%stxt' % domain, 'a') as fp:
            for i in records:
                fp.write('%s\n' % (i,))

        with open('domains_dnssec_%stxt' % domain, 'a') as fp:
            for i in dnssec_domains:
                fp.write('%s\n' % (i,))

    if onlyDNSSEC:
        return dnssec_domains
    else:
        return records


def usage():
    print("Usage: test.py <options>\n")
    print("Options:")
    print("   -h, --help                  Show this help message and exit")
    print("   -d, --domain       <domain> Domain to zonewalk")
    print("   -s, --start        <domain> Domain to start the zonewalk")
    print("   -n, --name_server  <name>   Domain server to use, if none is given the SOA is used")
    print("   -l  --lifetime     <number> Time to wait for a server to response to a query.")
    print("   -o, --output       <file>   Output file.")
    print("       --local        <file>   Option for checking if the domains in the given file are DNSSEC enabled.")
    print("       --once                  Just check the next NSEC for a specific hostname.")
    print("       --dnssec                Save only DNSSEC enabled domains from walked zone.")
    print("       --autosave              Save the list automatically under `data' folder.")
    sys.exit(0)

def main():
    global run_local
    global local_file
    global domain
    global onlyDNSSEC
    global autosave
    returned_records = []
    name_servers = []
    domain = None
    start = None
    ns_server = None
    request_timeout = 7.0
    out_file = None
    once = False
    onlyDNSSEC = False
    local_file = ''
    run_local = False
    autosave = False
    
    try:
        options, args = getopt.getopt(sys.argv[1:], 'hd:n:o:l:s:',
                                      ['help',
                                      'domain=',
                                      'name_server=',
                                      'output=',
                                      'start=',
                                      'once',
                                      'dnssec',
                                      'local=',
                                      'autosave',
                                      'lifetime='])

    except getopt.GetoptError:
        print_error("Wrong Option Provided!")
        usage()

    for opt, arg in options:
        if opt in ('-d', '--domain'):
            domain = arg

        elif opt in ('-n', '--name_server'):
            # Check if we got an IP or a FQDN
            if netaddr.valid_glob(arg):
                ns_server = arg
            else:
                # Resolve in the case if FQDN
                answer = socket_resolv(arg)
                # Check we actualy got a list
                if len(answer) > 0:
                    # We will use the first IP found as the NS
                    ns_server = answer[0][2]
                else:
                    # Exit if we cannot resolve it
                    print_error("Could not resolve NS server provided")
                    sys.exit(1)

        elif opt in ('-o', '--output'):
            out_file = arg

        elif opt in ('-s', '--start'):
            start = arg

        elif opt in ('--once'):
            once = True

        elif opt in ('--dnssec'):
            onlyDNSSEC = True

        elif opt in ('l', '--lifetime'):
            request_timeout = float(arg)

        elif opt in ('-h'):
            usage()

        elif opt in ('--local'):
            local_file = set(open(arg, 'r').read().split())
            run_local = True

        elif opt in ('--autosave'):
            autosave = True

    print "**************************************************"
    print "Zone: ", domain, " Starting point: ", start

    if start is None:
        """start = ("0_0.{0}".format(domain))"""
        start = domain

    # Set the resolver
    parent = start.split(".")[1]
    res = DnsHelper(domain, ns_server, request_timeout)

    # Enumerate Name Servers IPv4
    if ns_server is None:
        try:
            print "**************************************************"
            print "Enumerating NS"
            print datetime.datetime.now()
            for ns_rcrd in res.get_ns():
                if ":" not in ns_rcrd[2]:
                    name_servers.append(ns_rcrd[2]) 
                    print('\t {0} {1} {2}'.format(ns_rcrd[0], ns_rcrd[1], ns_rcrd[2]))      
            print datetime.datetime.now()
        except dns.resolver.NoAnswer:
            print_error("Could not Resolve NS Records for {0}".format(domain))
            print datetime.datetime.now()
    else:
        name_servers.append(ns_server)

        
    # Walk the zone  
    try:
        print datetime.datetime.now()
        if once is True:
            regNSEC = get_next(start, name_servers[0], request_timeout)
            if regNSEC is None:
                print "No NSEC found. Try appending a 0 to the hostname."
            else:
                print "next: ", regNSEC

        else:
            print "**************************************************"
            print "Walking the Zone"
            if out_file:
                returned_records.extend(ds_zone_walk(start, name_servers, request_timeout))
            else:
                ds_zone_walk(start, name_servers, request_timeout)
            print datetime.datetime.now()

    except dns.exception.Timeout:
        print_error("A timeout error occurred please make sure you can reach the target DNS Servers")
        print_error("directly and requests are not being filtered. Increase the timeout from {0} second".format(request_timeout))
        print_error("to a higher number with --lifetime <time> option.")
        print datetime.datetime.now()
        # sys.exit(1)

    # if an output file is specified it will write returned results.
    if out_file:
        print_status("Saving records to  file: {0}".format(out_file))
        write_to_file(returned_records, out_file)
        

if __name__ == "__main__":
    main()
