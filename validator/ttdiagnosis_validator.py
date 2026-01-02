import json
import sys
from enum import Enum


class DiagnosticValidation(Enum):
    """ Diagnostic validation status."""
    PASSED = "passed"
    FAILED = "failed"
    UNKNOWN = "unknown"


class DiagnosticTest:
    """ Base diagnostic test. Should not be instantiated."""
    def __init__(self):
        self.validation = None
        self.details = None

    @property
    def name(self):
        """ Returns the diagnostic name."""
        return self.__class__.__name__

    def to_dict(self):
        """ Returns the test results."""
        return {
            "validation": self.validation.value,
            "description": self.__class__.__doc__,
            "details": self.details
        }

    def run(self, diagnosis):
        """ Runs the test."""
        try:
            self.execute(diagnosis)
        except Exception as exc:
            self.validation = DiagnosticValidation.UNKNOWN
            self.details = repr(exc)

    def execute(self, diagnosis):
        """ Executes the test."""
        raise NotImplementedError


class GatewayProccessIsRunning(DiagnosticTest):
    """Gateway process is running."""
    def execute(self, diagnosis):
        self.validation = DiagnosticValidation.PASSED
        self.details = "Gateway application process is running."
        if diagnosis["proccesses"]["gateway"]["status"] != "Enabled":
            self.validation = DiagnosticValidation.FAILED
            self.details = "Gateway application proccess is not running."


class GatewayIsInit(DiagnosticTest):
    """Gateway is initialized."""
    def execute(self, diagnosis):
        self.validation = DiagnosticValidation.PASSED
        self.details = "Gateway is initialized."
        if not diagnosis["proccesses"]["gateway"]["status"]:
            self.validation = DiagnosticValidation.FAILED
            self.details = "Gateway is not initialized."


class GatewayFirmwareIsUpdated(DiagnosticTest):
    """Gateway firmware is updated."""
    def execute(self, diagnosis):
        self.validation = DiagnosticValidation.PASSED
        self.details = "Gateway firmware is updated."
        target_version = "1.5.0"
        version = diagnosis["proccesses"]["gateway"]["firmware"]["version"]
        target_version_parts = target_version.split('.')
        version_parts = version.split('.')
        target_version_numbers = [int(part) for part in target_version_parts]
        version_numbers = [int(part) for part in version_parts]
        if version_numbers < target_version_numbers:
            self.validation = DiagnosticValidation.FAILED
            self.details = "Gateway firmware is not updated." + \
                f"Firmware version: {version}." + \
                f"Last firmware version: {target_version}."


class GatewayLibraryIsUpdated(DiagnosticTest):
    """Gateway library is updated."""
    def execute(self, diagnosis):
        self.validation = DiagnosticValidation.PASSED
        self.details = "Gateway library is updated."
        target_version = "1.10.0"
        version = diagnosis["proccesses"]["gateway"]["library"]["version"]
        target_version_parts = target_version.split('.')
        version_parts = version.split('.')
        target_version_numbers = [int(part) for part in target_version_parts]
        version_numbers = [int(part) for part in version_parts]
        if version_numbers < target_version_numbers:
            self.validation = DiagnosticValidation.FAILED
            self.details = "Gateway library is not updated." + \
                f"Library version: {version}." + \
                f"Last library version: {target_version}."


class GatewayAppIsUpdated(DiagnosticTest):
    """Gateway application is updated."""
    def execute(self, diagnosis):
        self.validation = DiagnosticValidation.PASSED
        self.details = "Gateway application is updated."
        target_version = "1.12.0"
        version = diagnosis["proccesses"]["gateway"]["app"]["version"]
        target_version_parts = target_version.split('.')
        version_parts = version.split('.')
        target_version_numbers = [int(part) for part in target_version_parts]
        version_numbers = [int(part) for part in version_parts]
        if version_numbers < target_version_numbers:
            self.validation = DiagnosticValidation.FAILED
            self.details = "Gateway application is not updated." + \
                f"Application version: {version}." + \
                f"Last application version: {target_version}."


class BackendAppIsEnabled(DiagnosticTest):
    """Backend application is enabled."""
    def execute(self, diagnosis):
        self.validation = DiagnosticValidation.PASSED
        self.details = "Backend application is enabled."
        backend_app = diagnosis["proccesses"]["gateway"]["apps"]["backend"]
        if not backend_app:
            self.validation = DiagnosticValidation.FAILED
            self.details = "Backend application is not enabled."


class BleProccessIsRunning(DiagnosticTest):
    """Bluetooth configuration server proccess is running."""
    def execute(self, diagnosis):
        self.validation = DiagnosticValidation.PASSED
        self.details = "Bluetooth configuration server process is running."
        if diagnosis["proccesses"]["ble_config"]["status"] != "Enabled":
            self.validation = DiagnosticValidation.FAILED
            self.details = "Bluetooth config server proccess is not running."


class BleIsUpdated(DiagnosticTest):
    """Bluetooth configuration server is updated."""
    def execute(self, diagnosis):
        self.validation = DiagnosticValidation.PASSED
        self.details = "Bluetooth configuration server is updated."
        target_version = "1.0.0"
        version = diagnosis["proccesses"]["ble_config"]["version"]
        target_version_parts = target_version.split('.')
        version_parts = version.split('.')
        target_version_numbers = [int(part) for part in target_version_parts]
        version_numbers = [int(part) for part in version_parts]
        if version_numbers < target_version_numbers:
            self.validation = DiagnosticValidation.FAILED
            self.details = "Bluetooth configuration server is not updated." + \
                f"BLE configuration server version: {version}." + \
                f"Last BLE configuration server version: {target_version}."


class InternetIsConnected(DiagnosticTest):
    """Gateway is connected to the Internet."""
    def execute(self, diagnosis):
        connected = diagnosis["connection"]["connected"]
        interface = diagnosis["connection"]["interface"]
        self.validation = DiagnosticValidation.PASSED
        self.details = "Gateway is connected to the Internet throug the " + \
            f"{interface} interface."
        if not connected:
            self.validation = DiagnosticValidation.FAILED
            self.details = "Gateway is not connected to the Internet." + \
                "Available interfaces: "
            interfaces = diagnosis["interfaces"]
            for interface in interfaces:
                self.details += f"{interface['name']} "
            self.details += "."


class CpuUsageIsBelowLimit(DiagnosticTest):
    """Gateway CPU usage is below limit."""
    def execute(self, diagnosis):
        cpu_perc = diagnosis["system"]["cpu_perc"]
        cpu_perc_limit = 90
        self.validation = DiagnosticValidation.PASSED
        self.details = f"Gateway CPU usage is below the limit ({cpu_perc}%)."
        if cpu_perc > cpu_perc_limit:
            self.validation = DiagnosticValidation.FAILED
            self.details = "Gateway CPU usage is above the limit " + \
                f"({cpu_perc}%)."


class DiskAvailableBelowLimit(DiagnosticTest):
    """Gateway disk availability is below limit."""
    def execute(self, diagnosis):
        disk_avail = diagnosis["system"]["disk_available_mb"]
        disk_size = diagnosis["system"]["disk_size_mb"]
        disk_avail_perc = int(100 * disk_avail / disk_size)
        disk_avail_perc_lim = 10
        self.validation = DiagnosticValidation.PASSED
        self.details = "Gateway disk availability is above the limit: " + \
            f" {disk_avail}/{disk_size} MB ({disk_avail_perc}%)."
        if disk_avail_perc < disk_avail_perc_lim:
            self.validation = DiagnosticValidation.FAILED
            self.details = "Gateway disk availability is below the limit: " + \
                f" {disk_avail}/{disk_size} MB ({disk_avail_perc}%)."


class RamAvailableBelowLimit(DiagnosticTest):
    """Gateway ram availability is below limit."""
    def execute(self, diagnosis):
        ram_avail = diagnosis["system"]["ram_available_kb"]
        ram_size = diagnosis["system"]["ram_size_kb"]
        ram_avail_perc = int(100 * ram_avail / ram_size)
        ram_avail_perc_lim = 10
        self.validation = DiagnosticValidation.PASSED
        self.details = "Gateway RAM availability is above the limit: " + \
            f" {ram_avail}/{ram_size} MB ({ram_avail_perc}%)."
        if ram_avail_perc < ram_avail_perc_lim:
            self.validation = DiagnosticValidation.FAILED
            self.details = "Gateway disk availability is below the limit: " + \
                f" {ram_avail}/{ram_size} MB ({ram_avail_perc}%)."


class PingToInternetIsAvailable(DiagnosticTest):
    """Gateway has Internet ping."""
    def execute(self, diagnosis):
        self.validation = DiagnosticValidation.PASSED
        self.details = "Gateway has Internet ping."
        if not diagnosis["connection"]["ping"]["response"]:
            self.validation = DiagnosticValidation.FAILED
            self.details = "Gateway has not Internet ping."


class BluetoothModuleIsConnected(DiagnosticTest):
    """Gateway Bluetooth module connection is alive."""
    def execute(self, diagnosis):
        self.validation = DiagnosticValidation.PASSED
        self.details = "Gateway Bluetooth module connection is alive."
        if not diagnosis["gw_check"]["connection_alive"]:
            self.validation = DiagnosticValidation.FAILED
            self.details = "Gateway Bluetooth module is disconnected."


class ActiveNodesAreAboveLimit(DiagnosticTest):
    """Percentage of active nodes is above the limit."""
    def execute(self, diagnosis):
        nodes_active = diagnosis["node_summary"]["node_summary"]["nodes_active"]
        nodes_number = diagnosis["node_summary"]["node_summary"]["nodes_number"]
        perct_active = diagnosis["node_summary"]["node_summary"]["perct_active"]
        perct_active_lim = 95
        self.validation = DiagnosticValidation.PASSED
        self.details = "Percentage of active nodes is above the limit: " + \
            f" {nodes_active}/{nodes_number} ({perct_active}%)."
        if perct_active < perct_active_lim:
            self.validation = DiagnosticValidation.FAILED
            self.details = "Percentage of active nodes is below the limit " + \
                f"({perct_active_lim}%): {nodes_active}/{nodes_number} " + \
                f"({perct_active}%)."


class NodeCoverageIsRedundant(DiagnosticTest):
    """Node coverage is redundant."""
    def execute(self, diagnosis):
        node_coverage = diagnosis["proccesses"]["gateway"]["coverage"]
        non_redundant = 0
        for _, cvg_data in node_coverage.items():
            if len(cvg_data) < 2:
                non_redundant += 1
        network_len = len(node_coverage)
        redundant = len(node_coverage) - non_redundant
        network_redundancy = 100 * redundant / len(node_coverage)
        self.validation = DiagnosticValidation.PASSED
        if non_redundant:
            self.validation = DiagnosticValidation.FAILED
        self.details = "Percentage of node network redundancy: " + \
            f"{redundant}/{network_len} ({network_redundancy}%)."


tests = [
    GatewayProccessIsRunning(),
    GatewayIsInit(),
    GatewayFirmwareIsUpdated(),
    GatewayLibraryIsUpdated(),
    GatewayAppIsUpdated(),
    BackendAppIsEnabled(),
    BleProccessIsRunning(),
    BleIsUpdated(),
    InternetIsConnected(),
    CpuUsageIsBelowLimit(),
    DiskAvailableBelowLimit(),
    RamAvailableBelowLimit(),
    PingToInternetIsAvailable(),
    BluetoothModuleIsConnected(),
    ActiveNodesAreAboveLimit(),
    NodeCoverageIsRedundant()
]

def validate_diagnostics(diagnosis):
    """Performs a validation of the full diagnostic"""
    results = {}
    for test in tests:
        test.run(diagnosis)
        results[test.name] = test.to_dict()
    return results


def main():
    """Main function. Performs a diagnosis validation"""
    if len(sys.argv) < 2:
        print("usage: python3 ttdiagnosis_validator.py DIAGNOSIS_PATH ")
        sys.exit(1)
    with open(sys.argv[1], mode='r', encoding='utf-8') as file:
        json_data = json.load(file)
    results = validate_diagnostics(json_data)
    print(json.dumps(results, indent=2))

if __name__ == '__main__':
    main()
